from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

from app.models import db, Appointment, Patient, User, Lead, CRMCard, CRMStage, CRMHistory

agenda_bp = Blueprint('agenda_bp', __name__)

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def _get_clinic_id():
    identity = get_jwt_identity()

    if isinstance(identity, dict):
        cid = identity.get("clinic_id")
        try:
            return int(cid) if cid is not None else None
        except Exception:
            return None

    try:
        user_id = int(identity)
    except Exception:
        user_id = None

    if not user_id:
        return None

    user = User.query.get(user_id)
    return user.clinic_id if user else None


def _safe_iso_datetime(value: str):
    if not value:
        return None
    try:
        # aceita: "YYYY-MM-DDTHH:MM:SS" e também "YYYY-MM-DD HH:MM"
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _duration_to_timedelta_minutes(raw):
    """
    Heurística:
    - Se vier 30, 45, 60, 90 => minutos
    - Se vier 1, 2, 1.5 e <= 24 => horas (compat)
    """
    if raw in (None, "", 0):
        return timedelta(minutes=60)

    try:
        # aceita string/number
        if isinstance(raw, str) and raw.strip().isdigit():
            raw_num = int(raw.strip())
        else:
            raw_num = float(raw)

        # int pequeno típico de minutos (30/45/60/90/120/180)
        if isinstance(raw_num, (int,)) or (float(raw_num).is_integer()):
            raw_int = int(raw_num)
            if 1 <= raw_int <= 240:
                return timedelta(minutes=raw_int)

        # fallback horas compat
        if 0 < raw_num <= 24:
            return timedelta(hours=float(raw_num))

        # grandes => minutos
        return timedelta(minutes=int(raw_num))
    except Exception:
        return timedelta(minutes=60)


def _has_conflict(clinic_id: int, start_dt: datetime, end_dt: datetime, ignore_id: int | None = None):
    q = Appointment.query.filter_by(clinic_id=clinic_id)
    if ignore_id:
        q = q.filter(Appointment.id != ignore_id)

    # overlap: start < existing_end AND end > existing_start
    conflict = q.filter(
        Appointment.start_datetime < end_dt,
        Appointment.end_datetime > start_dt
    ).order_by(Appointment.start_datetime.asc()).first()

    return conflict


def _appt_to_dict(appt: Appointment, include_relations: bool = False):
    if hasattr(appt, "to_dict") and callable(getattr(appt, "to_dict")):
        base = appt.to_dict()
    else:
        base = {
            "id": appt.id,
            "clinic_id": appt.clinic_id,
            "patient_id": getattr(appt, "patient_id", None),
            "lead_id": getattr(appt, "lead_id", None),
            "title": getattr(appt, "title", None),
            "description": getattr(appt, "description", None),
            "start": appt.start_datetime.isoformat() if appt.start_datetime else None,
            "end": appt.end_datetime.isoformat() if appt.end_datetime else None,
            "status": getattr(appt, "status", None),
        }

    if include_relations:
        p = Patient.query.get(appt.patient_id) if appt.patient_id else None
        l = Lead.query.get(appt.lead_id) if appt.lead_id else None

        base["patient"] = {
            "id": p.id,
            "name": getattr(p, "name", None),
            "phone": getattr(p, "phone", None),
        } if p else None

        base["lead"] = {
            "id": l.id,
            "name": getattr(l, "name", None),
            "phone": getattr(l, "phone", None),
            "campaign_id": getattr(l, "campaign_id", None),
            "source": getattr(l, "source", None),
        } if l else None

    return base


def _get_lead_id_from_payload(data: dict):
    if not isinstance(data, dict):
        return None
    for key in ("lead_id", "marketing_lead_id"):
        if key in data and data.get(key) not in (None, "", 0):
            try:
                return int(data.get(key))
            except Exception:
                return None
    return None


def _move_lead_and_card_to_scheduled(clinic_id: int, lead: Lead | None, start_dt: datetime):
    """
    Move Lead.status e CRMCard.stage para "Agendado" baseado no telefone do lead.
    """
    if not lead:
        return

    lead.status = "agendado"

    # acha etapa
    stage_ag = CRMStage.query.filter_by(clinic_id=clinic_id, nome="Agendado").first()
    if not stage_ag:
        return

    # acha card pelo telefone
    phone = (lead.phone or "").strip()
    if not phone:
        return

    card = CRMCard.query.filter_by(clinic_id=clinic_id, paciente_phone=phone, status="open").first()
    if not card:
        return

    card.stage_id = stage_ag.id
    db.session.add(CRMHistory(
        card_id=card.id,
        tipo="status_change",
        descricao=f"Agendamento criado para {start_dt.strftime('%d/%m/%Y %H:%M')}"
    ))


# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------

@agenda_bp.route('/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    clinic_id = _get_clinic_id()
    if not clinic_id:
        return jsonify({"error": "clinic_id inválido no token"}), 401

    start_str = request.args.get('from')
    end_str = request.args.get('to')
    include = (request.args.get("include") or "").lower() in ("1", "true", "yes")

    query = Appointment.query.filter_by(clinic_id=clinic_id)

    start_dt = _safe_iso_datetime(start_str) if start_str else None
    end_dt = _safe_iso_datetime(end_str) if end_str else None

    if start_dt:
        query = query.filter(Appointment.start_datetime >= start_dt)
    if end_dt:
        query = query.filter(Appointment.start_datetime <= end_dt)

    appointments = query.order_by(Appointment.start_datetime.asc()).all()
    return jsonify([_appt_to_dict(a, include_relations=include) for a in appointments]), 200


@agenda_bp.route('/appointments', methods=['POST'])
@jwt_required()
def create_appointment():
    clinic_id = _get_clinic_id()
    if not clinic_id:
        return jsonify({"error": "clinic_id inválido no token"}), 401

    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "JSON inválido"}), 400

    start_raw = data.get("start") or data.get("start_datetime")
    start_dt = _safe_iso_datetime(start_raw)
    if not start_dt:
        return jsonify({"error": "Campo 'start' inválido (use ISO ou 'YYYY-MM-DD HH:MM')"}), 400

    end_raw = data.get("end") or data.get("end_datetime")
    end_dt = _safe_iso_datetime(end_raw)

    if not end_dt:
        delta = _duration_to_timedelta_minutes(data.get("duration"))
        end_dt = start_dt + delta

    # conflito
    conflict = _has_conflict(clinic_id, start_dt, end_dt)
    if conflict:
        return jsonify({
            "error": "Horário indisponível",
            "code": "TIME_CONFLICT",
            "conflict": _appt_to_dict(conflict)
        }), 409

    # ids
    patient_id = data.get("patient_id")
    try:
        patient_id = int(patient_id) if patient_id not in (None, "", 0) else None
    except Exception:
        patient_id = None

    lead_id = _get_lead_id_from_payload(data)

    if patient_id:
        patient = Patient.query.filter_by(id=patient_id, clinic_id=clinic_id).first()
        if not patient:
            return jsonify({"error": "patient_id não encontrado para esta clínica"}), 400

    lead = None
    if lead_id:
        lead = Lead.query.filter_by(id=lead_id, clinic_id=clinic_id).first()
        if not lead:
            return jsonify({"error": "lead_id não encontrado para esta clínica"}), 400

    title = (data.get('title') or data.get('patient_name') or "Agendamento").strip()
    description = (data.get('description') or data.get('procedure') or "").strip()
    status = (data.get('status') or "scheduled").strip()

    try:
        new_appt = Appointment(
            clinic_id=clinic_id,
            patient_id=patient_id,
            lead_id=lead_id,
            title=title,
            description=description,
            start_datetime=start_dt,
            end_datetime=end_dt,
            status=status
        )

        db.session.add(new_appt)

        # ✅ mover lead/card quando criado via CRM/Chatbot
        _move_lead_and_card_to_scheduled(clinic_id, lead, start_dt)

        db.session.commit()
        return jsonify(_appt_to_dict(new_appt, include_relations=True)), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Falha ao criar agendamento", "details": str(e)}), 400


@agenda_bp.route('/appointments/<int:id>', methods=['PATCH'])
@jwt_required()
def update_appointment(id):
    clinic_id = _get_clinic_id()
    if not clinic_id:
        return jsonify({"error": "clinic_id inválido no token"}), 401

    appt = Appointment.query.filter_by(id=id, clinic_id=clinic_id).first_or_404()
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "JSON inválido"}), 400

    try:
        start_dt = appt.start_datetime
        end_dt = appt.end_datetime

        if 'start' in data or 'start_datetime' in data:
            start_new = _safe_iso_datetime(data.get('start') or data.get('start_datetime'))
            if not start_new:
                return jsonify({"error": "start inválido"}), 400
            start_dt = start_new

        if 'end' in data or 'end_datetime' in data:
            end_new = _safe_iso_datetime(data.get('end') or data.get('end_datetime'))
            if not end_new:
                return jsonify({"error": "end inválido"}), 400
            end_dt = end_new
        elif 'duration' in data:
            end_dt = start_dt + _duration_to_timedelta_minutes(data.get("duration"))

        # conflito (ignorando o próprio)
        conflict = _has_conflict(clinic_id, start_dt, end_dt, ignore_id=appt.id)
        if conflict:
            return jsonify({
                "error": "Horário indisponível",
                "code": "TIME_CONFLICT",
                "conflict": _appt_to_dict(conflict)
            }), 409

        appt.start_datetime = start_dt
        appt.end_datetime = end_dt

        if 'title' in data:
            appt.title = (data.get('title') or "").strip()

        if 'description' in data:
            appt.description = (data.get('description') or "").strip()

        if 'status' in data:
            appt.status = (data.get('status') or "").strip()

        if 'patient_id' in data:
            pid = data.get('patient_id')
            try:
                pid = int(pid) if pid not in (None, "", 0) else None
            except Exception:
                pid = None

            if pid:
                patient = Patient.query.filter_by(id=pid, clinic_id=clinic_id).first()
                if not patient:
                    return jsonify({"error": "patient_id não encontrado para esta clínica"}), 400
            appt.patient_id = pid

        if 'lead_id' in data or 'marketing_lead_id' in data:
            lid = _get_lead_id_from_payload(data)
            if lid:
                lead = Lead.query.filter_by(id=lid, clinic_id=clinic_id).first()
                if not lead:
                    return jsonify({"error": "lead_id não encontrado para esta clínica"}), 400
            appt.lead_id = lid

        db.session.commit()
        return jsonify(_appt_to_dict(appt, include_relations=True)), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Falha ao atualizar agendamento", "details": str(e)}), 400


@agenda_bp.route('/appointments/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_appointment(id):
    clinic_id = _get_clinic_id()
    if not clinic_id:
        return jsonify({"error": "clinic_id inválido no token"}), 401

    appt = Appointment.query.filter_by(id=id, clinic_id=clinic_id).first_or_404()

    db.session.delete(appt)
    db.session.commit()
    return jsonify({"message": "Agendamento removido"}), 200
