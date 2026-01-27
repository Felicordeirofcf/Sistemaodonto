from flask import Blueprint, request, jsonify
from app.models import Patient, db
from flask_jwt_extended import jwt_required, get_jwt

patient_bp = Blueprint('patients', __name__)

# --- ROTA 1: LISTAR PACIENTES (GET) ---
@patient_bp.route('/patients', methods=['GET'])
@jwt_required()
def get_patients():
    claims = get_jwt()
    current_clinic_id = claims['clinic_id']
    
    try:
        patients = Patient.query.filter_by(clinic_id=current_clinic_id).all()
        
        output = []
        for p in patients:
            output.append({
                'id': p.id,
                'nome': p.name,
                'cpf': p.cpf,
                'telefone': p.phone,
                'status': p.status,
                'ultimaConsulta': p.last_visit.strftime('%d/%m/%Y') if p.last_visit else '-'
            })
        
        return jsonify(output), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- ROTA 2: CRIAR PACIENTE (POST) ---
@patient_bp.route('/patients', methods=['POST'])
@jwt_required()
def create_patient():
    claims = get_jwt()
    current_clinic_id = claims['clinic_id']
    data = request.get_json()
    
    if not data or 'nome' not in data:
        return jsonify({'error': 'Nome é obrigatório'}), 400

    new_patient = Patient(
        name=data['nome'],
        cpf=data.get('cpf', ''),
        phone=data.get('telefone', ''),
        clinic_id=current_clinic_id, # USA O ID DO TOKEN
        status='ativo'
    )
    
    try:
        db.session.add(new_patient)
        db.session.commit()
        return jsonify({'message': 'Paciente criado!', 'id': new_patient.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# --- ROTA 3: PEGAR DETALHES (GET) ---
@patient_bp.route('/patients/<int:id>', methods=['GET'])
@jwt_required()
def get_patient_details(id):
    claims = get_jwt()
    current_clinic_id = claims['clinic_id']
    
    # Garante que o paciente pertence à clínica de quem está pedindo
    patient = Patient.query.filter_by(id=id, clinic_id=current_clinic_id).first()
    
    if not patient:
        return jsonify({'error': 'Paciente não encontrado ou acesso negado'}), 404
        
    return jsonify({
        'id': patient.id,
        'nome': patient.name,
        'cpf': patient.cpf,
        'odontogram_data': patient.odontogram_data or {}
    })

# --- ROTA 4: SALVAR ODONTOGRAMA (PUT) ---
@patient_bp.route('/patients/<int:id>/odontogram', methods=['PUT'])
@jwt_required()
def save_odontogram(id):
    claims = get_jwt()
    current_clinic_id = claims['clinic_id']
    
    patient = Patient.query.filter_by(id=id, clinic_id=current_clinic_id).first()
    
    if not patient:
        return jsonify({'error': 'Acesso negado'}), 404
    
    patient.odontogram_data = request.get_json()
    db.session.commit()
    return jsonify({'message': 'Salvo!'}), 200