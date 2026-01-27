from flask import Blueprint, request, jsonify
from app.models import db, User, Clinic
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt, get_jwt_identity

auth_bp = Blueprint('auth', __name__)

# 1. REGISTRAR NOVA CLÍNICA (Fluxo Self-Service)
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email já cadastrado'}), 400
        
    try:
        # Tratamento do documento para evitar erro de UNIQUE constraint
        cnpj_cpf_val = data.get('document')
        if not cnpj_cpf_val: 
            cnpj_cpf_val = None 
            
        # Define o limite de dentistas baseado no plano escolhido
        # Exemplo: bronze=1, silver=5, gold=10
        plan = data.get('plan_type', 'bronze')
        limits = {'bronze': 1, 'silver': 5, 'gold': 10}
        max_dentists = limits.get(plan, 1)

        # 1. Cria a Clínica com limites de plano
        new_clinic = Clinic(
            name=data['clinic_name'],
            cnpj_cpf=cnpj_cpf_val,
            plan_type=plan,
            max_dentists=max_dentists, # Configurado automaticamente
            is_active=True
        )
        db.session.add(new_clinic)
        db.session.flush() 
        
        # 2. Cria o Usuário Administrador (Dono da Clínica)
        new_user = User(
            name=data['user_name'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            role='admin', # Dono tem permissão total
            clinic_id=new_clinic.id
        )
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'message': 'Conta e clínica criadas com sucesso!'}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Erro no registro: {str(e)}")
        return jsonify({'error': 'Erro ao processar registro.'}), 500

# 2. LOGIN COM PERMISSÕES (RBAC)
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    
    if not user or not check_password_hash(user.password_hash, data.get('password')):
        return jsonify({'error': 'Credenciais inválidas'}), 401
        
    # Bloqueio de Inadimplência
    if not user.clinic.is_active:
        return jsonify({"msg": "Sua clínica está inativa. Verifique o pagamento."}), 403

    # O Token agora carrega a ROLE (admin/dentist) para o Frontend
    access_token = create_access_token(
        identity=str(user.id), 
        additional_claims={
            'clinic_id': user.clinic_id, 
            'role': user.role 
        }
    )
    
    return jsonify({
        'token': access_token,
        'role': user.role, # Para o React saber o que mostrar
        'user': {
            'name': user.name,
            'clinic': user.clinic.name,
            'plan': user.clinic.plan_type
        }
    }), 200

# 3. ADICIONAR DENTISTA (COM VERIFICAÇÃO DE LIMITE)
@auth_bp.route('/add-dentist', methods=['POST'])
@jwt_required()
def add_dentist():
    claims = get_jwt()
    # Apenas admin pode adicionar outros usuários
    if claims['role'] != 'admin':
        return jsonify({"error": "Acesso negado"}), 403
    
    data = request.get_json()
    user_admin = User.query.get(get_jwt_identity())
    clinic = user_admin.clinic

    # Verifica se atingiu o limite do plano
    dentist_count = User.query.filter_by(clinic_id=clinic.id, role='dentist').count()
    if dentist_count >= clinic.max_dentists:
        return jsonify({
            "error": f"Limite atingido! Seu plano ({clinic.plan_type}) permite apenas {clinic.max_dentists} dentistas."
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
    return jsonify({"message": "Dentista cadastrado com sucesso!"}), 201