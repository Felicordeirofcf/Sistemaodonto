from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, AutomacaoRecall, Clinic, CRMStage, CRMCard, Patient
from datetime import datetime

bp = Blueprint("marketing_automations", __name__)

# ==============================================================================
# 1. ROTAS DE AUTOMAÇÃO (ROBÔ)
# ==============================================================================

# --- LISTAR REGRAS ---
@bp.route('/automations', methods=['GET'])
@jwt_required()
def list_automations():
    identity = get_jwt_identity()
    clinic_id = identity.get("clinic_id") if isinstance(identity, dict) else 1
    
    regras = AutomacaoRecall.query.filter_by(clinic_id=clinic_id).all()
    
    return jsonify([{
        "id": r.id,
        "nome": r.nome,
        "dias_ausente": r.dias_ausente,
        "horario": r.horario_disparo,
        "mensagem": r.mensagem_template,
        "ativo": r.ativo
    } for r in regras]), 200

# --- CRIAR NOVA REGRA ---
@bp.route('/automations', methods=['POST'])
@jwt_required()
def create_automation():
    identity = get_jwt_identity()
    clinic_id = identity.get("clinic_id") if isinstance(identity, dict) else 1
    
    data = request.get_json()
    
    nova_regra = AutomacaoRecall(
        clinic_id=clinic_id,
        nome=data.get("nome", "Nova Regra"),
        dias_ausente=int(data.get("dias_ausente", 180)),
        horario_disparo=data.get("horario", "09:00"),
        mensagem_template=data.get("mensagem", "Olá {nome}, faz tempo que não te vemos!"),
        ativo=True
    )
    
    db.session.add(nova_regra)
    db.session.commit()
    
    return jsonify({"message": "Regra criada com sucesso!"}), 201

# --- DELETAR REGRA ---
@bp.route('/automations/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_automation(id):
    regra = AutomacaoRecall.query.get_or_404(id)
    db.session.delete(regra)
    db.session.commit()
    return jsonify({"message": "Regra removida"}), 200


# ==============================================================================
# 2. ROTAS DO CRM (KANBAN)
# ==============================================================================

@bp.route('/crm/board', methods=['GET'])
@jwt_required()
def get_crm_board():
    identity = get_jwt_identity()
    clinic_id = identity.get("clinic_id") if isinstance(identity, dict) else 1

    # 1. Verifica se existem estágios (Colunas). Se não, CRIA OS PADRÕES.
    estagios = CRMStage.query.filter_by(clinic_id=clinic_id).order_by(CRMStage.ordem).all()
    
    if not estagios:
        padroes = [
            {"nome": "A Contactar", "cor": "yellow", "ordem": 1, "is_initial": True},
            {"nome": "Aguardando Resposta", "cor": "blue", "ordem": 2, "is_initial": False},
            {"nome": "Agendado", "cor": "green", "ordem": 3, "is_initial": False, "is_success": True},
            {"nome": "Perdido", "cor": "red", "ordem": 4, "is_initial": False}
        ]
        for p in padroes:
            novo_estagio = CRMStage(
                clinic_id=clinic_id, 
                nome=p["nome"], 
                cor=p["cor"], 
                ordem=p["ordem"],
                is_initial=p.get("is_initial", False),
                is_success=p.get("is_success", False)
            )
            db.session.add(novo_estagio)
        db.session.commit()
        # Busca de novo agora que criou
        estagios = CRMStage.query.filter_by(clinic_id=clinic_id).order_by(CRMStage.ordem).all()

    # 2. Monta o objeto do Kanban com os Cards
    board_data = []
    
    for estagio in estagios:
        # Busca cards deste estágio
        cards = CRMCard.query.filter_by(stage_id=estagio.id).all()
        cards_data = []
        
        for card in cards:
            paciente = Patient.query.get(card.paciente_id)
            cards_data.append({
                "id": card.id,
                "paciente_nome": paciente.name if paciente else "Desconhecido",
                "paciente_phone": paciente.phone if paciente else "",
                "ultima_interacao": card.ultima_interacao.strftime("%d/%m %H:%M"),
                "status": card.status
            })
            
        board_data.append({
            "id": estagio.id,
            "nome": estagio.nome,
            "cor": estagio.cor,
            "cards": cards_data
        })

    return jsonify(board_data), 200