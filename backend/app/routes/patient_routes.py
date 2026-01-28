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
        
        # Filtra apenas pacientes da clínica do usuário
        patients = Patient.query.filter_by(clinic_id=user.clinic_id).all()
        return jsonify([p.to_dict() for p in patients]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- CRIAR PACIENTE (CORREÇÃO DO ERRO 405) ---
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
        
        return jsonify(new_patient.to_dict()), 201

    except Exception as e:
        db.session.rollback()
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
        # Retorna também o histórico de consultas
        appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(Appointment.date_time.desc()).all()
        patient_data = patient.to_dict()
        patient_data['history'] = [a.to_dict() for a in appointments]
        return jsonify(patient_data), 200

    if request.method == 'PUT':
        data = request.get_json()
        patient.name = data.get('name', patient.name)
        patient.phone = data.get('phone', patient.phone)
        patient.email = data.get('email', patient.email)
        patient.address = data.get('address', patient.address)
        db.session.commit()
        return jsonify(patient.to_dict()), 200

    if request.method == 'DELETE':
        db.session.delete(patient)
        db.session.commit()
        return jsonify({'message': 'Paciente removido'}), 200