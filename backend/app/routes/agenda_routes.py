from flask import Blueprint, jsonify, request
from app.models import db, Appointment, Transaction, Patient, User, Procedure, Lead
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
            'end': appt.date_time.isoformat(),
            'status': appt.status,
            'price': appt.price,
            'is_paid': appt.is_paid
        })
    return jsonify(output), 200

# 2. WEBHOOK PARA O CHATBOT (MARCAR CONSULTA AUTOMÁTICA)
@agenda_bp.route('/webhooks/chatbot-booking', methods=['POST'])
def chatbot_booking():
    data = request.get_json()
    # Esperamos: name, phone, date (ISO), service, clinic_id
    
    try:
        # Busca ou cria o paciente profissionalmente
        patient = Patient.query.filter_by(phone=data['phone'], clinic_id=data['clinic_id']).first()
        if not patient:
            patient = Patient(
                name=data['name'], 
                phone=data['phone'], 
                source='Chatbot-IA', # Rastreio para o marketing
                clinic_id=data['clinic_id']
            )
            db.session.add(patient)
            db.session.flush()

        # Cria o agendamento
        new_appt = Appointment(
            patient_id=patient.id,
            clinic_id=data['clinic_id'],
            date_time=datetime.fromisoformat(data['date']),
            service=data['service'],
            status='agendado'
        )
        db.session.add(new_appt)

        # Move o Lead no CRM para "Consulta Agendada"
        new_lead = Lead(
            clinic_id=data['clinic_id'],
            name=data['name'],
            phone=data['phone'],
            source='Bot-WhatsApp',
            status='scheduled' # Coluna: Consulta Agendada
        )
        db.session.add(new_lead)
        
        db.session.commit()
        return jsonify({"message": "Sincronização Bot-Agenda-CRM concluída!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# 3. FINALIZAR CONSULTA (COM BAIXA DE INSUMOS E LUCRO REAL)
@agenda_bp.route('/appointments/<int:id>/finish', methods=['PUT'])
@jwt_required()
def finish_appointment(id):
    user = User.query.get(get_jwt_identity())
    appt = Appointment.query.filter_by(id=id, clinic_id=user.clinic_id).first()
    
    if not appt: return jsonify({'error': 'Consulta não encontrada'}), 404
    
    data = request.get_json()
    appt.status = 'concluido'
    
    # --- LÓGICA DE INSUMOS (OPCIONAL SE O SERVIÇO TIVER RECEITA) ---
    total_material_cost = 0
    procedure = Procedure.query.filter_by(name=appt.service, clinic_id=user.clinic_id).first()
    
    if procedure:
        for req in procedure.requirements:
            # Baixa automática no estoque
            req.item.quantity -= req.quantity_needed
            # Calcula o custo baseado no preço de compra
            total_material_cost += (req.item.purchase_price * req.quantity_needed)

    # --- LANÇAMENTO FINANCEIRO COM LUCRO LÍQUIDO ---
    if not appt.is_paid:
        appt.is_paid = True
        new_transaction = Transaction(
            clinic_id=user.clinic_id,
            description=f"Atendimento: {appt.patient.name} ({appt.service})",
            amount=appt.price,
            cost=total_material_cost, # Agora o lucro é real!
            type='income',
            category='Tratamento',
            appointment_id=appt.id,
            date=datetime.utcnow()
        )
        db.session.add(new_transaction)
    
    # Atualiza o status do lead no CRM para "Em Tratamento"
    lead = Lead.query.filter_by(phone=appt.patient.phone, clinic_id=user.clinic_id).first()
    if lead:
        lead.status = 'treating'

    db.session.commit()
    return jsonify({'message': 'Consulta finalizada, estoque baixado e lucro calculado!'}), 200