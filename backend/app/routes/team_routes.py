from flask import Blueprint, jsonify, request
from app.models import db, User, Clinic
from flask_jwt_extended import jwt_required, get_jwt_identity

team_bp = Blueprint('team', __name__)

# 1. ROTA DE ESTATÍSTICAS (Resolve o erro 404 dos logs)
@team_bp.route('/clinic/team-stats', methods=['GET'])
@jwt_required()
def get_team_stats():
    try:
        user_id = get_jwt_identity()
        current_user = User.query.get(user_id)
        
        # Conta dentistas e funcionários vinculados à mesma clínica
        dentists_count = User.query.filter_by(
            clinic_id=current_user.clinic_id, 
            role='dentist'
        ).count()
        
        total_staff = User.query.filter_by(
            clinic_id=current_user.clinic_id
        ).count()

        return jsonify({
            'dentists_count': dentists_count,
            'total_staff': total_staff,
            'limit_reached': dentists_count >= (current_user.clinic.max_dentists or 1)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 2. LISTAR MEMBROS DA EQUIPE
@team_bp.route('/clinic/team', methods=['GET'])
@jwt_required()
def list_team():
    user_id = get_jwt_identity()
    current_user = User.query.get(user_id)
    
    team = User.query.filter_by(clinic_id=current_user.clinic_id).all()
    
    return jsonify([{
        'id': u.id,
        'name': u.user_name,
        'email': u.email,
        'role': u.role,
        'is_active': True # No futuro pode vir do banco
    } for u in team]), 200