from flask import Blueprint, jsonify, request
from app.models import db, Patient, User, Appointment
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

patient_bp = Blueprint('patient', __name__)

# --- LISTAR PACIENTES (GET) ---
@patient_bp.route('/patients', methods=['GET'])
@jwt_required()
def get_patients():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        # Filtra apenas pacientes da clínica do usuário
        patients = Patient.query.filter_by(clinic_id=user.clinic_id).order_by(Patient.name).all()
        
        # Garante que to_dict() existe no model, senão cria manual
        result = []
        for p in patients:
            p_dict = p.to_dict() if hasattr(p, 'to_dict') else {
                'id': p.id,
                'name': p.name,
                'phone': p.phone,
                'cpf': p.cpf,
                'email': p.email,
                'address': p.address
            }
            result.append(p_dict)

        return jsonify(result), 200
    except Exception as e:
        print(f"Erro ao listar pacientes: {e}") # Log no terminal
        return jsonify({'error': str(e)}), 500

# --- CRIAR PACIENTE (POST) ---
@patient_bp.route('/patients', methods=['POST'])
@jwt_required()
def create_patient():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        data = request.get_json()

        # Validação básica
        if not data.get('name') or not data.get('phone'):
            return jsonify({'error': 'Nome e Telefone são obrigatórios'}), 400

        new_patient = Patient(
            clinic_id=user.clinic_id,
            name=data.get('name'),
            phone=data.get('phone'),
            email=data.get('email'),
            cpf=data.get('cpf'),
            address=data.get('address'),
            created_at=datetime.utcnow()
        )

        db.session.add(new_patient)
        db.session.commit()
        
        # Retorna dicionário seguro
        response_data = new_patient.to_dict() if hasattr(new_patient, 'to_dict') else {
            'id': new_patient.id, 'name': new_patient.name
        }
        return jsonify(response_data), 201

    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar paciente: {e}")
        return jsonify({'error': f"Erro ao criar paciente: {str(e)}"}), 500

# --- DETALHES/EDITAR/DELETAR (PUT, DELETE) ---
@patient_bp.route('/patients/<int:id>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def manage_patient(id):
    user = User.query.get(get_jwt_identity())
    patient = Patient.query.filter_by(id=id, clinic_id=user.clinic_id).first()

    if not patient:
        return jsonify({'error': 'Paciente não encontrado'}), 404

    if request.method == 'GET':
        # Tenta pegar histórico, se der erro retorna lista vazia
        try:
            appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.date_time.desc()).all()
            history = [a.to_dict() for a in appointments]
        except:
            history = []

        patient_data = patient.to_dict() if hasattr(patient, 'to_dict') else {
            'id': patient.id, 'name': patient.name, 'phone': patient.phone, 'cpf': patient.cpf, 'email': patient.email, 'address': patient.address
        }
        patient_data['history'] = history
        return jsonify(patient_data), 200

    if request.method == 'PUT':
        data = request.get_json()
        patient.name = data.get('name', patient.name)
        patient.phone = data.get('phone', patient.phone)
        patient.email = data.get('email', patient.email)
        patient.address = data.get('address', patient.address)
        # CPF geralmente não se muda, mas se quiser permitir:
        if data.get('cpf'):
            patient.cpf = data.get('cpf')
            
        db.session.commit()
        return jsonify(patient.to_dict() if hasattr(patient, 'to_dict') else {'msg': 'ok'}), 200

    if request.method == 'DELETE':
        db.session.delete(patient)
        db.session.commit()
        return jsonify({'message': 'Paciente removido'}), 200