from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

from app.models import db, Appointment, Patient, User, Lead

agenda_bp = Blueprint('agenda_bp', __name__)

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def _get_clinic_id():
    """
    Suporta JWT identity como:
    - dict com clinic_id
    - user_id (int/str) que referencia User.id
    """
    identity = get_jwt_identity()

    if isinstance(identity, dict):
        cid = identity.get("clinic_id")
        try:
            return int(cid) if cid is not None else None
        except Exception:
            return None

    # fallback: identity = user_id
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
        return datetime.fromisoformat(value)
    except Exception:
        return None


def _appt_to_dict(appt: Appointment, include_relations: bool = False):
    """
    Usa appt.to_dict() se existir; senão monta manualmente.
    """
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

    # normaliza chaves esperadas no front
    if "start_datetime" in base and "start" not in base:
        base["start"] = base.get("start_datetime")
    if "end_datetime" in base and "end" not in base:
        base["end"] = base.get("end_datetime")

    if include_relations:
        # patient
        p = None
        pid = getattr(appt, "patient_id", None)
        if pid:
            p = Patient.query.get(pid)

        # lead (marketing_leads)
        l = None
        lid = getattr(appt, "lead_id", None)
        if lid:
            l = Lead.query.get(lid)

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
    """
    Compatibilidade:
    - lead_id (atual)
    - marketing_lead_id (caso você renomeie)
    """
    if not isinstance(data, dict):
        return None
    for key in ("lead_id", "marketing_lead_id"):
        if key in data and data.get(key) not in (None, "", 0):
            try:
                return int(data.get(key))
            except Exception:
                return None
    return None


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

    start_dt = _safe_iso_datetime(start_str)
    end_dt = _safe_iso_datetime(end_str)

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
        return jsonify({"error": "Campo 'start' inválido (use ISO, ex: 2026-02-03T09:00:00)"}), 400

    end_raw = data.get("end") or data.get("end_datetime")
    end_dt = _safe_iso_datetime(end_raw)

    if not end_dt:
        # Default duration 1h (ou duration enviado)
        try:
            duration_h = float(data.get('duration', 1))
        except Exception:
            duration_h = 1.0
        end_dt = start_dt + timedelta(hours=duration_h)

    # ids
    patient_id = data.get("patient_id")
    try:
        patient_id = int(patient_id) if patient_id not in (None, "", 0) else None
    except Exception:
        patient_id = None

    lead_id = _get_lead_id_from_payload(data)

    # (opcional) validações de existência por clínica
    if patient_id:
        patient = Patient.query.filter_by(id=patient_id, clinic_id=clinic_id).first()
        if not patient:
            return jsonify({"error": "patient_id não encontrado para esta clínica"}), 400

    if lead_id:
        # Lead é marketing_leads, mas ainda tem clinic_id no seu model
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
        if 'start' in data or 'start_datetime' in data:
            start_dt = _safe_iso_datetime(data.get('start') or data.get('start_datetime'))
            if not start_dt:
                return jsonify({"error": "start inválido"}), 400
            appt.start_datetime = start_dt

        if 'end' in data or 'end_datetime' in data:
            end_dt = _safe_iso_datetime(data.get('end') or data.get('end_datetime'))
            if not end_dt:
                return jsonify({"error": "end inválido"}), 400
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

        # compat: lead_id / marketing_lead_id
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
