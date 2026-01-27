from flask import Blueprint, request, jsonify
from app.models import db, User, Clinic
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

auth_bp = Blueprint('auth', __name__)

# 1. REGISTRAR NOVA CLÍNICA (Sign Up)
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validação: Email já existe?
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email já cadastrado'}), 400
        
    try:
        # --- CORREÇÃO DO ERRO DE CONSTRAINT ---
        # document = data.get('document')
        # Se for vazio, transformamos em None (null no banco)
        # O banco permite múltiplos nulls, mas não permite múltiplos "" vazios
        cnpj_cpf_val = data.get('document')
        if not cnpj_cpf_val: 
            cnpj_cpf_val = None 
            
        # 1. Cria a Clínica
        new_clinic = Clinic(
            name=data['clinic_name'],
            cnpj_cpf=cnpj_cpf_val # Usa a variável tratada
        )
        db.session.add(new_clinic)
        db.session.flush() # Gera o ID para usar abaixo
        
        # 2. Cria o Usuário Admin
        new_user = User(
            name=data['user_name'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role='admin',
            clinic_id=new_clinic.id
        )
        db.session.add(new_user)
        
        db.session.commit()
        
        return jsonify({'message': 'Conta criada com sucesso!'}), 201
    except Exception as e:
        db.session.rollback()
        # Dica de Debug: Mostra o erro real no console se der ruim de novo
        print(f"Erro no registro: {str(e)}")
        return jsonify({'error': 'Erro ao criar conta. Tente outro email ou contate o suporte.'}), 500

# 2. LOGIN (Sign In)
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Email ou senha inválidos'}), 401
        
    if not user.clinic.is_active:
        return jsonify({'error': 'Sua clínica está inativa'}), 403

    # Gera o Token
    access_token = create_access_token(
        identity=str(user.id), 
        additional_claims={'clinic_id': user.clinic_id, 'role': user.role}
    )
    
    return jsonify({
        'token': access_token,
        'user': {
            'name': user.name,
            'email': user.email,
            'clinic': user.clinic.name
        }
    }), 200