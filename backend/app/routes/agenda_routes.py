from flask import Blueprint, jsonify, request
from app.models import db, Appointment, Transaction, Patient, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

agenda_bp = Blueprint('agenda_bp', __name__)

# 1. LISTAR CONSULTAS
@agenda_bp.route('/appointments', methods=['GET'])
@jwt_required()
def get_appointments():
    user = User.query.get(get_jwt_identity())
    appointments = Appointment.query.filter_by(clinic_id=user.clinic_id).all()
    
    output = []
    for appt in appointments:
        # Nota: Ajustando campos baseados no modelo Appointment real
        output.append({
            'id': appt.id,
            'title': f"{appt.patient_name or (appt.patient.name if appt.patient else 'Paciente')} - {appt.procedure}",
            'start': appt.date_time.isoformat(),
            'end': appt.date_time.isoformat(),
            'status': appt.status
        })
    return jsonify(output), 200

# 2. WEBHOOK PARA O CHATBOT (MARCAR CONSULTA AUTOMÁTICA)
@agenda_bp.route('/webhooks/chatbot-booking', methods=['POST'])
def chatbot_booking():
    data = request.get_json()
    
    try:
        # Busca ou cria o paciente profissionalmente
        patient = Patient.query.filter_by(phone=data['phone'], clinic_id=data['clinic_id']).first()
        if not patient:
            patient = Patient(
                name=data['name'], 
                phone=data['phone'], 
                source='Chatbot-IA',
                clinic_id=data['clinic_id']
            )
            db.session.add(patient)
            db.session.flush()

        # Cria o agendamento
        new_appt = Appointment(
            patient_id=patient.id,
            clinic_id=data['clinic_id'],
            date_time=datetime.fromisoformat(data['date']),
            procedure=data['service'],
            status='agendado'
        )
        db.session.add(new_appt)
        
        db.session.commit()
        return jsonify({"message": "Sincronização Bot-Agenda concluída!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# 3. FINALIZAR CONSULTA
@agenda_bp.route('/appointments/<int:id>/finish', methods=['PUT'])
@jwt_required()
def finish_appointment(id):
    user = User.query.get(get_jwt_identity())
    appt = Appointment.query.filter_by(id=id, clinic_id=user.clinic_id).first()
    
    if not appt: return jsonify({'error': 'Consulta não encontrada'}), 404
    
    appt.status = 'concluido'
    
    # Lógica simplificada de transação financeira
    new_transaction = Transaction(
        clinic_id=user.clinic_id,
        description=f"Atendimento: {appt.patient_name or (appt.patient.name if appt.patient else 'Paciente')} ({appt.procedure})",
        amount=0.0, # Valor deve ser preenchido ou vir do front
        type='income',
        category='Tratamento',
        date=datetime.utcnow()
    )
    db.session.add(new_transaction)
    
    db.session.commit()
    return jsonify({'message': 'Consulta finalizada!'}), 200
