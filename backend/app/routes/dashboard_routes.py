from flask import Blueprint, jsonify
from app.models import db, Patient, InventoryItem, Transaction, Lead, User, Appointment
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_stats():
    claims = get_jwt()
    current_clinic_id = claims['clinic_id']
    
    # 1. Estatísticas Básicas
    total_patients = Patient.query.filter_by(clinic_id=current_clinic_id).count()
    low_stock_count = InventoryItem.query.filter(
        InventoryItem.clinic_id == current_clinic_id,
        InventoryItem.quantity <= InventoryItem.min_quantity
    ).count()
    
    # 2. Financeiro Real (Soma das transações de hoje)
    hoje = datetime.utcnow().date()
    transacoes_hoje = Transaction.query.filter(
        Transaction.clinic_id == current_clinic_id,
        db.func.date(Transaction.date) == hoje
    ).all()
    
    faturamento_dia = sum(t.amount for t in transacoes_hoje if t.type == 'income')
    lucro_dia = sum((t.amount - t.cost) for t in transacoes_hoje if t.type == 'income')
    
    # 3. Consultas do dia
    agendamentos_hoje = Appointment.query.filter(
        Appointment.clinic_id == current_clinic_id,
        db.func.date(Appointment.date_time) == hoje
    ).count()

    return jsonify({
        'patients': total_patients,
        'low_stock': low_stock_count,
        'revenue': faturamento_dia,
        'net_profit': lucro_dia,
        'appointments': agendamentos_hoje
    })

@dashboard_bp.route('/dashboard/conversion-stats', methods=['GET'])
@jwt_required()
def get_conversion_stats():
    user = User.query.get(get_jwt_identity())
    
    # Leads captados pelo Chatbot
    bot_leads = Lead.query.filter_by(clinic_id=user.clinic_id, source='Chatbot-IA').count()
    
    # Conversões (Pacientes que vieram do bot e concluíram consulta)
    converted_patients = Patient.query.filter_by(clinic_id=user.clinic_id, source='Chatbot-IA').all()
    
    total_revenue_bot = 0
    total_profit_bot = 0
    conversions_count = 0

    for patient in converted_patients:
        for appt in patient.appointments_list:
            if appt.status == 'concluido':
                conversions_count += 1
                transaction = Transaction.query.filter_by(appointment_id=appt.id).first()
                if transaction:
                    total_revenue_bot += transaction.amount
                    total_profit_bot += (transaction.amount - transaction.cost)

    return jsonify({
        'leads_generated': bot_leads,
        'conversions': conversions_count,
        'conversion_rate': (conversions_count / bot_leads * 100) if bot_leads > 0 else 0,
        'revenue': total_revenue_bot,
        'net_profit': total_profit_bot
    }), 200