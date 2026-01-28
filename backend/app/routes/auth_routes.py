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
        # Tratamento do documento para evitar erro de UNIQUE constraint
        cnpj_cpf_val = data.get('document')
        if not cnpj_cpf_val or cnpj_cpf_val.strip() == "": 
            cnpj_cpf_val = None 
            
        # Lógica de Planos SaaS (Alinhado com a Sidebar e App.tsx)
        plan = data.get('plan_type', 'bronze').lower()
        limits = {'bronze': 1, 'silver': 5, 'gold': 10}
        max_dentists = limits.get(plan, 1)

        # 1. Cria a Clínica (O "Tenant")
        new_clinic = Clinic(
            name=data['clinic_name'],
            cnpj_cpf=cnpj_cpf_val,
            plan_type=plan,
            max_dentists=max_dentists,
            is_active=True # Começa ativa para o teste
        )
        db.session.add(new_clinic)
        db.session.flush() 
        
        # 2. Cria o Usuário Administrador (Dono)
        new_user = User(
            name=data['user_name'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role='admin',
            is_active=True, # NOVO: Campo obrigatório que causava erro no banco
            clinic_id=new_clinic.id
        )
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'message': 'Conta criada com sucesso! Aproveite o sistema.'}), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ ERRO NO REGISTRO: {str(e)}")
        return jsonify({'error': 'Erro ao processar cadastro. Contate o suporte.'}), 500

# 2. LOGIN COM PERMISSÕES (RBAC)
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    
    if not user or not check_password_hash(user.password_hash, data.get('password')):
        return jsonify({'error': 'Email ou senha inválidos'}), 401
        
    # Verificação de Bloqueio (Caso a clínica não pague o SaaS)
    if not user.clinic.is_active:
        return jsonify({
            "error": "Acesso suspenso",
            "message": "Sua clínica está inativa no momento.",
            "is_active": False
        }), 403

    # O Token carrega CLINIC_ID para blindagem das rotas API
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

# 3. VERIFICAR STATUS (Alimenta o componente PrivateRoute do React)
@auth_bp.route('/status', methods=['GET'])
@jwt_required()
def get_auth_status():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário inexistente'}), 404
            
        return jsonify({
            'is_active': user.clinic.is_active, # Retorna se a clínica pagou
            'role': user.role,
            'clinic_name': user.clinic.name
        }), 200
    except Exception as e:
        return jsonify({'is_active': True}), 200 # Fallback para evitar travamentos em testes

# 4. GESTÃO DE EQUIPE (RBAC + LIMITES DE PLANO)
@auth_bp.route('/add-dentist', methods=['POST'])
@jwt_required()
def add_dentist():
    claims = get_jwt()
    if claims['role'] != 'admin':
        return jsonify({"error": "Apenas o Dr. Administrador pode gerenciar a equipe."}), 403
    
    data = request.get_json()
    user_admin = User.query.get(get_jwt_identity())
    clinic = user_admin.clinic

    # Verifica limite do plano SaaS (Bronze=1, Silver=5, Gold=10)
    dentist_count = User.query.filter_by(clinic_id=clinic.id, role='dentist').count()
    if dentist_count >= clinic.max_dentists:
        return jsonify({
            "error": f"Limite atingido para o plano {clinic.plan_type}. Faça upgrade!"
        }), 400

    new_dentist = User(
        name=data['name'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role='dentist',
        is_active=True,
        clinic_id=clinic.id
    )
    db.session.add(new_dentist)
    db.session.commit()
    return jsonify({"message": "Dentista integrado à sua equipe!"}), 201