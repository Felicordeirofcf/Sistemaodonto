from flask import Blueprint, jsonify, request
from app.models import db, Lead, User
from flask_jwt_extended import jwt_required, get_jwt_identity

marketing_bp = Blueprint('marketing_bp', __name__)

# 1. LISTAR LEADS (GET)
@marketing_bp.route('/marketing/leads', methods=['GET'])
@jwt_required()
def get_leads():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Filtra apenas leads da clínica do usuário logado
    leads = Lead.query.filter_by(clinic_id=user.clinic_id).all()
    
    return jsonify([lead.to_dict() for lead in leads]), 200

# 2. CRIAR NOVO LEAD (POST)
@marketing_bp.route('/marketing/leads', methods=['POST'])
@jwt_required()
def create_lead():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    data = request.get_json()
    
    new_lead = Lead(
        clinic_id=user.clinic_id,
        name=data.get('name'),
        phone=data.get('phone'),
        source=data.get('source', 'Manual'),
        status='new', # Todo lead começa como 'Novo'
        notes=data.get('notes', '')
    )
    
    db.session.add(new_lead)
    db.session.commit()
    
    return jsonify(new_lead.to_dict()), 201

# 3. MOVER CARD (ATUALIZAR STATUS) (PUT)
@marketing_bp.route('/marketing/leads/<int:id>/move', methods=['PUT'])
@jwt_required()
def move_lead(id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    data = request.get_json()
    
    # Busca o lead e garante que pertence à clínica do usuário
    lead = Lead.query.filter_by(id=id, clinic_id=user.clinic_id).first()
    
    if not lead:
        return jsonify({'error': 'Lead não encontrado'}), 404
        
    lead.status = data.get('status')
    db.session.commit()
    
    return jsonify({'message': 'Status atualizado com sucesso!'}), 200