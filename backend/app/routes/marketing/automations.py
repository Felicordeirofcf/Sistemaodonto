from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, AutomacaoRecall, Clinic

bp = Blueprint("marketing_automations", __name__)

# --- LISTAR REGRAS ---
@bp.route('/automations', methods=['GET'])
@jwt_required()
def list_automations():
    identity = get_jwt_identity()
    # Tratamento seguro do ID da clínica
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