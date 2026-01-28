from flask import Blueprint, jsonify, request
from app.models import db, User, Clinic
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash

team_bp = Blueprint('team', __name__)

# 1. ROTA DE ESTATÍSTICAS (Fornece metadados do plano SaaS)
@team_bp.route('/clinic/team-stats', methods=['GET'])
@jwt_required()
def get_team_stats():
    try:
        user_id = get_jwt_identity()
        current_user = User.query.get(user_id)
        
        if not current_user or not current_user.clinic:
            return jsonify({'error': 'Clínica não encontrada'}), 404

        # Conta dentistas vinculados à clínica
        dentists_count = User.query.filter_by(
            clinic_id=current_user.clinic_id, 
            role='dentist'
        ).count()
        
        return jsonify({
            'dentists_count': dentists_count,
            'max_dentists': current_user.clinic.max_dentists or 1,
            'plan_type': current_user.clinic.plan_type if hasattr(current_user.clinic, 'plan_type') else 'Bronze',
            'limit_reached': dentists_count >= (current_user.clinic.max_dentists or 1)
        }), 200
    except Exception as e:
        print(f"Erro Team Stats: {str(e)}")
        return jsonify({'error': 'Erro interno ao processar estatísticas'}), 500

# 2. LISTAR MEMBROS DA EQUIPE (Resolvendo o Erro 500)
@team_bp.route('/clinic/team', methods=['GET'])
@jwt_required()
def list_team():
    try:
        user_id = get_jwt_identity()
        current_user = User.query.get(user_id)
        
        if not current_user:
            return jsonify({'error': 'Usuário não autorizado'}), 401

        team = User.query.filter_by(clinic_id=current_user.clinic_id).all()
        
        output = []
        for u in team:
            # CORREÇÃO: Usando 'name' conforme identificado no seu banco
            output.append({
                'id': u.id,
                'name': getattr(u, 'name', u.email), 
                'email': u.email,
                'role': u.role,
                'is_active': getattr(u, 'is_active', True)
            })
            
        return jsonify(output), 200
    except Exception as e:
        print(f"Erro List Team: {str(e)}") 
        return jsonify({'error': 'Erro ao listar membros da equipe'}), 500

# 3. CADASTRAR NOVO PROFISSIONAL (Com Trava de Plano)
@team_bp.route('/clinic/team', methods=['POST'])
@jwt_required()
def create_team_member():
    try:
        user_id = get_jwt_identity()
        admin_user = User.query.get(user_id)
        data = request.get_json()

        # Validação de Limite do Plano
        if data.get('role') == 'dentist':
            current_dentists = User.query.filter_by(
                clinic_id=admin_user.clinic_id, 
                role='dentist'
            ).count()
            
            limit = admin_user.clinic.max_dentists or 1
            if current_dentists >= limit:
                return jsonify({
                    'error': f'Limite atingido para o plano {admin_user.clinic.plan_type}.'
                }), 403

        # Verificação de e-mail duplicado
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Este e-mail já está cadastrado.'}), 400

        # Criação usando 'name' e gerando hash seguro
        new_member = User(
            name=data.get('name') or data.get('user_name'),
            email=data['email'],
            role=data.get('role', 'dentist'),
            clinic_id=admin_user.clinic_id,
            password_hash=generate_password_hash(data.get('password', '123456'))
        )

        db.session.add(new_member)
        db.session.commit()

        return jsonify({'id': new_member.id, 'message': 'Cadastrado com sucesso!'}), 201

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar membro: {str(e)}")
        return jsonify({'error': 'Erro interno ao processar cadastro.'}), 500