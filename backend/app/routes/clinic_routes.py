from flask import Blueprint, jsonify
from app.models import db, User, Clinic
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity

clinic_bp = Blueprint('clinic', __name__)

@clinic_bp.route('/clinic/team-stats', methods=['GET'])
@jwt_required()
def get_team_stats():
    claims = get_jwt()
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Busca a clínica do usuário logado
    clinic = user.clinic
    
    # Lista todos os membros da equipe daquela clínica
    members = User.query.filter_by(clinic_id=clinic.id).all()
    
    # Conta apenas os que possuem cargo de dentista para o limite do plano
    dentist_count = User.query.filter_by(clinic_id=clinic.id, role='dentist').count()

    return jsonify({
        'plan_type': clinic.plan_type,
        'max_dentists': clinic.max_dentists,
        'current_count': dentist_count,
        'members': [{
            'id': m.id,
            'name': m.name,
            'email': m.email,
            'role': m.role
        } for m in members]
    }), 200