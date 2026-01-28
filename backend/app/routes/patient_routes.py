from flask import Blueprint, request, jsonify
from app.models import Patient, db
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from app.models import User

patient_bp = Blueprint('patients', __name__)

# Helper para pegar clinic_id de forma robusta
def get_current_clinic():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user.clinic_id if user else None

# --- ROTA 1: LISTAR PACIENTES (GET) ---
@patient_bp.route('/patients', methods=['GET'])
@jwt_required()
def get_patients():
    clinic_id = get_current_clinic()
    if not clinic_id:
        return jsonify({'error': 'Clínica não identificada'}), 401
    
    try:
        patients = Patient.query.filter_by(clinic_id=clinic_id).all()
        
        output = []
        for p in patients:
            output.append({
                'id': p.id,
                'name': p.name, # Mantendo 'name' para bater com o banco
                'nome': p.name, # Alias para evitar erro de 'em branco' no frontend
                'cpf': p.cpf,
                'telefone': p.phone,
                'email': p.email,
                'status': getattr(p, 'status', 'ativo'),
                'origem': getattr(p, 'source', 'Manual'),
                'ultimaConsulta': p.last_visit.strftime('%d/%m/%Y') if hasattr(p, 'last_visit') and p.last_visit else '-'
            })
        
        return jsonify(output), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- ROTA 2 & 4: PEGAR DETALHES OU ATUALIZAR (GET/PUT) ---
# Esta rota resolve o erro 405 (Method Not Allowed)
@patient_bp.route('/patients/<int:id>', methods=['GET', 'PUT'])
@jwt_required()
def handle_patient_detail(id):
    clinic_id = get_current_clinic()
    patient = Patient.query.filter_by(id=id, clinic_id=clinic_id).first()
    
    if not patient:
        return jsonify({'error': 'Paciente não encontrado'}), 404
        
    if request.method == 'PUT':
        try:
            data = request.get_json()
            # Atualização flexível (pode ser odontograma ou dados básicos)
            if 'name' in data: patient.name = data['name']
            if 'nome' in data: patient.name = data['nome']
            if 'phone' in data: patient.phone = data['phone']
            if 'odontogram_data' in data: 
                patient.odontogram_data = data['odontogram_data'] # Salva o estado dos dentes
            
            db.session.commit()
            return jsonify({'message': 'Dados atualizados com sucesso!'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # Retorno para o GET
    return jsonify({
        'id': patient.id,
        'name': patient.name,
        'nome': patient.name,
        'cpf': patient.cpf,
        'telefone': patient.phone,
        'email': patient.email,
        'odontogram_data': patient.odontogram_data or {} # Carrega para o canvas 3D
    }), 200

# --- ROTA 3: SALVAR ODONTOGRAMA ESPECÍFICO (OPCIONAL) ---
@patient_bp.route('/patients/<int:id>/odontogram', methods=['PUT'])
@jwt_required()
def save_odontogram_legacy(id):
    clinic_id = get_current_clinic()
    patient = Patient.query.filter_by(id=id, clinic_id=clinic_id).first()
    
    if not patient:
        return jsonify({'error': 'Acesso negado'}), 404
    
    try:
        data = request.get_json()
        # Se os dados vierem direto como objeto ou dentro da chave
        patient.odontogram_data = data.get('odontogram_data', data)
        db.session.commit()
        return jsonify({'message': 'Odontograma salvo!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500