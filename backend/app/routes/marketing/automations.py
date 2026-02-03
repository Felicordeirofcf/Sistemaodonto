from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, AutomacaoRecall, CRMStage, CRMCard, Patient
from datetime import datetime

bp = Blueprint("marketing_automations", __name__)

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def _get_clinic_id_from_jwt():
    identity = get_jwt_identity()
    if isinstance(identity, dict) and identity.get("clinic_id"):
        return identity["clinic_id"]
    return 1

def _get_json_or_400():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


# ==============================================================================
# 1. ROTAS DE AUTOMAÇÃO (ROBÔ)
# ==============================================================================

@bp.route('/automations', methods=['GET'])
@jwt_required()
def list_automations():
    clinic_id = _get_clinic_id_from_jwt()

    regras = AutomacaoRecall.query.filter_by(clinic_id=clinic_id).all()

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
    data = _get_json_or_400()
    if data is None:
        return jsonify({"message": "JSON inválido ou ausente"}), 400

    # Validações mínimas para não estourar exceptions
    try:
        dias_ausente = int(data.get("dias_ausente", 180))
    except Exception:
        dias_ausente = 180

    horario = (data.get("horario") or "09:00").strip()
    nome = (data.get("nome") or "Nova Regra").strip()
    mensagem = (data.get("mensagem") or "Olá {nome}, faz tempo que não te vemos!").strip()

    # (Opcional) valida formato HH:MM
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

    return jsonify({
        "message": "Regra criada com sucesso!",
        "id": nova_regra.id
    }), 201


@bp.route('/automations/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_automation(id):
    clinic_id = _get_clinic_id_from_jwt()

    # Segurança multi-tenant: não deixa deletar regra de outra clínica
    regra = AutomacaoRecall.query.filter_by(id=id, clinic_id=clinic_id).first()
    if not regra:
        return jsonify({"message": "Regra não encontrada"}), 404

    db.session.delete(regra)
    db.session.commit()
    return jsonify({"message": "Regra removida"}), 200


def _is_valid_time_hhmm(value: str) -> bool:
    # Aceita "09:00" / "9:00" (se quiser exigir 2 dígitos, ajusta)
    try:
        datetime.strptime(value, "%H:%M")
        return True
    except Exception:
        return False


# ==============================================================================
# 2. ROTAS DO CRM (KANBAN)
# ==============================================================================

@bp.route('/crm/board', methods=['GET'])
@jwt_required()
def get_crm_board():
    clinic_id = _get_clinic_id_from_jwt()

    # 1) Estágios do funil (cria default se não existir)
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

    # 2) Busca todos cards da clínica de uma vez (evita N+1 e vazamento)
    stage_ids = [e.id for e in estagios]

    cards = CRMCard.query.filter(
        CRMCard.clinic_id == clinic_id,
        CRMCard.stage_id.in_(stage_ids)
    ).all()

    # 3) Carrega pacientes em lote
    paciente_ids = {c.paciente_id for c in cards if c.paciente_id}
    pacientes = Patient.query.filter(Patient.id.in_(paciente_ids)).all() if paciente_ids else []
    pacientes_map = {p.id: p for p in pacientes}

    # 4) Indexa cards por estágio
    cards_by_stage = {sid: [] for sid in stage_ids}
    for card in cards:
        cards_by_stage.setdefault(card.stage_id, []).append(card)

    # 5) Monta resposta
    board_data = []
    for estagio in estagios:
        cards_data = []
        for card in cards_by_stage.get(estagio.id, []):
            paciente = pacientes_map.get(card.paciente_id)

            ultima = card.ultima_interacao
            ultima_fmt = ultima.strftime("%d/%m %H:%M") if ultima else ""

            cards_data.append({
                "id": card.id,
                "paciente_nome": paciente.name if paciente else (card.paciente_nome or "Desconhecido"),
                "paciente_phone": paciente.phone if paciente else (card.paciente_phone or ""),
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
