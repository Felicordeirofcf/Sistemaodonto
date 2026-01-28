from flask import Blueprint, jsonify, request
from app.models import db, User, Clinic
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash

team_bp = Blueprint('team', __name__)

# 1. ROTA DE ESTATÍSTICAS (Resolve o 404 e fornece metadados do plano)
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
        
        # Verificação segura de atributos para evitar o erro 500
        output = []
        for u in team:
            output.append({
                'id': u.id,
                'name': getattr(u, 'user_name', u.email), # Fallback para email se nome for null
                'email': u.email,
                'role': u.role,
                'is_active': getattr(u, 'is_active', True)
            })
            
        return jsonify(output), 200
    except Exception as e:
        print(f"Erro List Team: {str(e)}") 
        return jsonify({'error': 'Erro ao listar membros da equipe'}), 500

# 3. CADASTRAR NOVO MEMBRO (Rota POST com Trava de Plano SaaS)
@team_bp.route('/clinic/team', methods=['POST'])
@jwt_required()
def create_team_member():
    try:
        user_id = get_jwt_identity()
        admin_user = User.query.get(user_id)
        data = request.get_json()

        # Validação de Limite do Plano SaaS
        if data.get('role') == 'dentist':
            current_dentists = User.query.filter_by(
                clinic_id=admin_user.clinic_id, 
                role='dentist'
            ).count()
            
            limit = admin_user.clinic.max_dentists or 1
            
            if current_dentists >= limit:
                return jsonify({
                    'error': f'Limite de dentistas atingido para o plano {admin_user.clinic.plan_type}.'
                }), 403

        # Verificação de e-mail duplicado no banco
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Este e-mail já está cadastrado no sistema.'}), 400

        # Criação do novo usuário vinculado à clínica
        new_member = User(
            user_name=data['name'],
            email=data['email'],
            role=data.get('role', 'dentist'),
            clinic_id=admin_user.clinic_id,
            # Gera hash seguro da senha (padrão 123456 ou enviada)
            password_hash=generate_password_hash(data.get('password', '123456'))
        )

        db.session.add(new_member)
        db.session.commit()

        return jsonify({
            'id': new_member.id,
            'name': new_member.user_name,
            'email': new_member.email,
            'role': new_member.role
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar membro: {str(e)}")
        return jsonify({'error': 'Erro interno ao processar cadastro.'}), 500