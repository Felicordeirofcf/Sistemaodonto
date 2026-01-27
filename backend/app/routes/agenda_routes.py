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
        output.append({
            'id': appt.id,
            'title': f"{appt.patient.name} - {appt.service}",
            'start': appt.date_time.isoformat(),
            'end': appt.date_time.isoformat(), # Simplificado, ideal seria somar duração
            'status': appt.status,
            'price': appt.price,
            'is_paid': appt.is_paid
        })
    return jsonify(output), 200

# 2. CRIAR CONSULTA
@agenda_bp.route('/appointments', methods=['POST'])
@jwt_required()
def create_appointment():
    user = User.query.get(get_jwt_identity())
    data = request.get_json()
    
    # Converte string ISO para objeto datetime
    dt_object = datetime.fromisoformat(data['date_time'].replace('Z', ''))

    new_appt = Appointment(
        clinic_id=user.clinic_id,
        patient_id=data['patient_id'],
        date_time=dt_object,
        service=data.get('service', 'Consulta'),
        price=float(data.get('price', 0.0)),
        status='agendado'
    )
    
    db.session.add(new_appt)
    db.session.commit()
    return jsonify({'message': 'Agendado com sucesso!'}), 201

# 3. FINALIZAR E SINCRONIZAR FINANCEIRO (A MÁGICA 🎩)
@agenda_bp.route('/appointments/<int:id>/finish', methods=['PUT'])
@jwt_required()
def finish_appointment(id):
    user = User.query.get(get_jwt_identity())
    appt = Appointment.query.filter_by(id=id, clinic_id=user.clinic_id).first()
    
    if not appt: return jsonify({'error': 'Consulta não encontrada'}), 404
    
    data = request.get_json()
    pagou_agora = data.get('pay_now', False) # Checkbox "Receber agora"
    
    appt.status = 'concluido'
    
    # Se o usuário marcou que recebeu, cria a transação
    if pagou_agora and not appt.is_paid:
        appt.is_paid = True
        
        # CRIA O LANÇAMENTO NO FINANCEIRO AUTOMATICAMENTE
        new_transaction = Transaction(
            clinic_id=user.clinic_id,
            description=f"Recebimento: {appt.patient.name} ({appt.service})",
            amount=appt.price,
            type='income', # Entrada
            category='Tratamento',
            appointment_id=appt.id,
            date=datetime.utcnow()
        )
        db.session.add(new_transaction)
    
    db.session.commit()
    return jsonify({'message': 'Consulta finalizada e financeiro atualizado!'}), 200