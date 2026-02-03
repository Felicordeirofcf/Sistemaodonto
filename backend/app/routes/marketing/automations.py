from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, AutomacaoRecall, CRMStage, CRMCard, Patient
from datetime import datetime

bp = Blueprint("marketing_automations", __name__)

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def _get_clinic_id_from_jwt() -> int:
    identity = get_jwt_identity()
    if isinstance(identity, dict) and identity.get("clinic_id"):
        try:
            return int(identity["clinic_id"])
        except Exception:
            return 1
    return 1

def _get_json_or_none():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None

def _is_valid_time_hhmm(value: str) -> bool:
    try:
        datetime.strptime(value, "%H:%M")
        return True
    except Exception:
        return False

def _clamp_int(value, default=180, min_v=1, max_v=3650):
    try:
        v = int(value)
        if v < min_v: return min_v
        if v > max_v: return max_v
        return v
    except Exception:
        return default


# ==============================================================================
# 1. ROTAS DE AUTOMAÇÃO (ROBÔ)
# ==============================================================================

@bp.route('/automations', methods=['GET'])
@jwt_required()
def list_automations():
    clinic_id = _get_clinic_id_from_jwt()

    regras = AutomacaoRecall.query.filter_by(clinic_id=clinic_id).order_by(AutomacaoRecall.id.desc()).all()

    return jsonify([{
        "id": r.id,
        "nome": r.nome,
        "dias_ausente": r.dias_ausente,
        "horario": r.horario_disparo,
        "mensagem": r.mensagem_template,
        "ativo": bool(r.ativo)
    } for r in regras]), 200


@bp.route('/automations', methods=['POST'])
@jwt_required()
def create_automation():
    clinic_id = _get_clinic_id_from_jwt()
    data = _get_json_or_none()
    if data is None:
        return jsonify({"message": "JSON inválido ou ausente"}), 400

    nome = (data.get("nome") or "Nova Regra").strip()
    horario = (data.get("horario") or "09:00").strip()
    mensagem = (data.get("mensagem") or "Olá {nome}, faz tempo que não te vemos!").strip()
    dias_ausente = _clamp_int(data.get("dias_ausente", 180), default=180, min_v=1, max_v=3650)

    if not _is_valid_time_hhmm(horario):
        return jsonify({"message": "Horário inválido. Use HH:MM (ex: 09:00)."}), 400

    nova_regra = AutomacaoRecall(
        clinic_id=clinic_id,
        nome=nome,
        dias_ausente=dias_ausente,
        horario_disparo=horario,
        mensagem_template=mensagem,
        ativo=True
    )

    db.session.add(nova_regra)
    db.session.commit()

    return jsonify({"message": "Regra criada com sucesso!", "id": nova_regra.id}), 201


@bp.route('/automations/<int:id>', methods=['PATCH'])
@jwt_required()
def update_automation(id):
    """
    Atualiza parcialmente uma regra:
    - nome
    - dias_ausente
    - horario
    - mensagem
    - ativo
    """
    clinic_id = _get_clinic_id_from_jwt()
    data = _get_json_or_none()
    if data is None:
        return jsonify({"message": "JSON inválido ou ausente"}), 400

    regra = AutomacaoRecall.query.filter_by(id=id, clinic_id=clinic_id).first()
    if not regra:
        return jsonify({"message": "Regra não encontrada"}), 404

    if "nome" in data:
        regra.nome = (data.get("nome") or "Nova Regra").strip()

    if "dias_ausente" in data:
        regra.dias_ausente = _clamp_int(data.get("dias_ausente", regra.dias_ausente), default=regra.dias_ausente)

    if "horario" in data:
        horario = (data.get("horario") or "").strip()
        if not _is_valid_time_hhmm(horario):
            return jsonify({"message": "Horário inválido. Use HH:MM (ex: 09:00)."}), 400
        regra.horario_disparo = horario

    if "mensagem" in data:
        regra.mensagem_template = (data.get("mensagem") or "").strip()

    if "ativo" in data:
        regra.ativo = bool(data.get("ativo"))

    db.session.commit()

    return jsonify({
        "message": "Regra atualizada",
        "id": regra.id,
        "ativo": bool(regra.ativo)
    }), 200


@bp.route('/automations/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_automation(id):
    clinic_id = _get_clinic_id_from_jwt()

    regra = AutomacaoRecall.query.filter_by(id=id, clinic_id=clinic_id).first()
    if not regra:
        return jsonify({"message": "Regra não encontrada"}), 404

    db.session.delete(regra)
    db.session.commit()
    return jsonify({"message": "Regra removida"}), 200


# ==============================================================================
# 2. ROTAS DO CRM (KANBAN)
# ==============================================================================

@bp.route('/crm/board', methods=['GET'])
@jwt_required()
def get_crm_board():
    clinic_id = _get_clinic_id_from_jwt()

    # 1) Estágios (cria default se não existir)
    estagios = CRMStage.query.filter_by(clinic_id=clinic_id).order_by(CRMStage.ordem).all()

    if not estagios:
        padroes = [
            {"nome": "A Contactar", "cor": "yellow", "ordem": 1, "is_initial": True},
            {"nome": "Aguardando Resposta", "cor": "blue", "ordem": 2},
            {"nome": "Agendado", "cor": "green", "ordem": 3, "is_success": True},
            {"nome": "Perdido", "cor": "red", "ordem": 4}
        ]
        for p in padroes:
            db.session.add(CRMStage(
                clinic_id=clinic_id,
                nome=p["nome"],
                cor=p["cor"],
                ordem=p["ordem"],
                is_initial=p.get("is_initial", False),
                is_success=p.get("is_success", False)
            ))
        db.session.commit()
        estagios = CRMStage.query.filter_by(clinic_id=clinic_id).order_by(CRMStage.ordem).all()

    stage_ids = [e.id for e in estagios]

    # 2) Busca cards da clínica em lote
    cards = CRMCard.query.filter(
        CRMCard.clinic_id == clinic_id,
        CRMCard.stage_id.in_(stage_ids)
    ).all()

    # 3) Pacientes em lote
    paciente_ids = {c.paciente_id for c in cards if getattr(c, "paciente_id", None)}
    pacientes = Patient.query.filter(Patient.id.in_(paciente_ids)).all() if paciente_ids else []
    pacientes_map = {p.id: p for p in pacientes}

    # 4) Indexa por stage
    cards_by_stage = {sid: [] for sid in stage_ids}
    for card in cards:
        cards_by_stage.setdefault(card.stage_id, []).append(card)

    # 5) Monta resposta
    board_data = []
    for estagio in estagios:
        cards_data = []
        for card in cards_by_stage.get(estagio.id, []):
            paciente = pacientes_map.get(getattr(card, "paciente_id", None))

            ultima = getattr(card, "ultima_interacao", None)
            ultima_fmt = ultima.strftime("%d/%m %H:%M") if ultima else ""

            cards_data.append({
                "id": card.id,
                "paciente_nome": (paciente.name if paciente else (getattr(card, "paciente_nome", None) or "Desconhecido")),
                "paciente_phone": (paciente.phone if paciente else (getattr(card, "paciente_phone", None) or "")),
                "ultima_interacao": ultima_fmt,
                "status": card.status
            })

        board_data.append({
            "id": estagio.id,
            "nome": estagio.nome,
            "cor": estagio.cor,
            "cards": cards_data
        })

    return jsonify(board_data), 200
