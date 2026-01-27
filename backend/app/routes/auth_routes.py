from flask import Blueprint, request, jsonify
from app.models import db, User, Clinic
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt, get_jwt_identity

auth_bp = Blueprint('auth', __name__)

# 1. REGISTRAR NOVA CLÍNICA (Fluxo Self-Service)
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validação Básica
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Este email já está cadastrado em nosso sistema'}), 400
        
    try:
        # Tratamento do documento para evitar erro de UNIQUE constraint no banco
        cnpj_cpf_val = data.get('document')
        if not cnpj_cpf_val or cnpj_cpf_val.strip() == "": 
            cnpj_cpf_val = None 
            
        # Lógica de Planos SaaS
        plan = data.get('plan_type', 'bronze')
        limits = {'bronze': 1, 'silver': 5, 'gold': 10}
        max_dentists = limits.get(plan, 1)

        # 1. Cria a Clínica (O "Tenant")
        new_clinic = Clinic(
            name=data['clinic_name'],
            cnpj_cpf=cnpj_cpf_val,
            plan_type=plan,
            max_dentists=max_dentists,
            is_active=True # Clínica começa ativa
        )
        db.session.add(new_clinic)
        db.session.flush() # Flush para obter o ID da clínica antes do commit final
        
        # 2. Cria o Usuário Administrador (Dono)
        new_user = User(
            name=data['user_name'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role='admin',
            clinic_id=new_clinic.id
        )
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'message': 'Conta e clínica criadas com sucesso! Bem-vindo.'}), 201

    except Exception as e:
        db.session.rollback()
        # Log detalhado para o seu console do Render
        print(f"ERRO CRÍTICO NO REGISTRO: {str(e)}")
        return jsonify({'error': 'Erro interno ao processar cadastro. Verifique os dados ou contate o suporte.'}), 500

# 2. LOGIN COM PERMISSÕES (RBAC)
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    
    if not user or not check_password_hash(user.password_hash, data.get('password')):
        return jsonify({'error': 'Email ou senha inválidos'}), 401
        
    # Verificação de Inadimplência / Status da Clínica
    if not user.clinic.is_active:
        return jsonify({
            "error": "Acesso suspenso",
            "message": "Sua clínica está inativa. Regularize sua assinatura.",
            "is_active": False
        }), 403

    # O Token carrega a ROLE e CLINIC_ID para blindagem das rotas API
    access_token = create_access_token(
        identity=str(user.id), 
        additional_claims={
            'clinic_id': user.clinic_id, 
            'role': user.role 
        }
    )
    
    return jsonify({
        'token': access_token,
        'role': user.role,
        'user': {
            'name': user.name,
            'clinic': user.clinic.name,
            'plan': user.clinic.plan_type,
            'is_active': user.clinic.is_active
        }
    }), 200

# 3. VERIFICAR STATUS (Usado pelo PrivateRoute do React)
@auth_bp.route('/status', methods=['GET'])
@jwt_required()
def get_auth_status():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
        
    return jsonify({
        'is_active': user.clinic.is_active,
        'role': user.role
    }), 200

# 4. ADICIONAR DENTISTA (Gestão de Equipe)
@auth_bp.route('/add-dentist', methods=['POST'])
@jwt_required()
def add_dentist():
    claims = get_jwt()
    if claims['role'] != 'admin':
        return jsonify({"error": "Acesso negado. Apenas administradores podem gerenciar a equipe."}), 403
    
    data = request.get_json()
    user_admin = User.query.get(get_jwt_identity())
    clinic = user_admin.clinic

    # Verifica limite do plano SaaS antes de permitir o novo registro
    dentist_count = User.query.filter_by(clinic_id=clinic.id, role='dentist').count()
    if dentist_count >= clinic.max_dentists:
        return jsonify({
            "error": f"Limite de dentistas atingido para o seu plano ({clinic.plan_type})."
        }), 400

    new_dentist = User(
        name=data['name'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role='dentist',
        clinic_id=clinic.id
    )
    db.session.add(new_dentist)
    db.session.commit()
    return jsonify({"message": "Novo dentista adicionado à equipe!"}), 201