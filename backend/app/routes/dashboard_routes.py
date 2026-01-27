from flask import Blueprint, jsonify
from app.models import db, Patient, InventoryItem, Transaction, Lead, User, Appointment
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_stats():
    try:
        claims = get_jwt()
        current_clinic_id = claims['clinic_id']
        
        # 1. Estatísticas Básicas
        total_patients = Patient.query.filter_by(clinic_id=current_clinic_id).count() or 0
        
        # Coalesce garante que se min_quantity for NULL, ele use 0 para a comparação
        low_stock_count = InventoryItem.query.filter(
            InventoryItem.clinic_id == current_clinic_id,
            InventoryItem.quantity <= db.func.coalesce(InventoryItem.min_quantity, 0)
        ).count() or 0
        
        # 2. Financeiro do Dia
        hoje = datetime.utcnow().date()
        transacoes_hoje = Transaction.query.filter(
            Transaction.clinic_id == current_clinic_id,
            db.func.date(Transaction.date) == hoje
        ).all()
        
        # Somas seguras tratando explicitamente tipos para o Frontend
        faturamento_dia = sum(float(t.amount or 0) for t in transacoes_hoje if t.type == 'income') if transacoes_hoje else 0.0
        lucro_dia = sum(float((t.amount or 0) - (t.cost or 0)) for t in transacoes_hoje if t.type == 'income') if transacoes_hoje else 0.0
        
        # 3. Consultas do dia
        agendamentos_hoje = Appointment.query.filter(
            Appointment.clinic_id == current_clinic_id,
            db.func.date(Appointment.date_time) == hoje
        ).count() or 0

        return jsonify({
            'patients': int(total_patients),
            'low_stock': int(low_stock_count),
            'revenue': float(faturamento_dia),
            'net_profit': float(lucro_dia),
            'appointments': int(agendamentos_hoje)
        }), 200

    except Exception as e:
        # Log detalhado para o Render
        print(f"ERRO CRÍTICO DASHBOARD: {str(e)}")
        return jsonify({'error': 'Erro ao carregar indicadores do painel'}), 500

@dashboard_bp.route('/dashboard/conversion-stats', methods=['GET'])
@jwt_required()
def get_conversion_stats():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
            
        clinic_id = user.clinic_id
        
        # Leads captados pelo Chatbot
        bot_leads = Lead.query.filter_by(clinic_id=clinic_id, source='Chatbot-IA').count() or 0
        
        # Conversões do Bot
        converted_patients = Patient.query.filter_by(clinic_id=clinic_id, source='Chatbot-IA').all()
        
        total_revenue_bot = 0.0
        total_profit_bot = 0.0
        conversions_count = 0

        for patient in converted_patients:
            appts = getattr(patient, 'appointments_list', [])
            for appt in appts:
                if appt.status == 'concluido':
                    conversions_count += 1
                    transaction = Transaction.query.filter_by(appointment_id=appt.id).first()
                    if transaction:
                        total_revenue_bot += float(transaction.amount or 0)
                        total_profit_bot += float((transaction.amount or 0) - (transaction.cost or 0))

        # Divisão segura
        rate = (conversions_count / bot_leads * 100) if bot_leads > 0 else 0

        return jsonify({
            'leads_generated': int(bot_leads),
            'conversions': int(conversions_count),
            'conversion_rate': round(float(rate), 2),
            'revenue': float(total_revenue_bot),
            'net_profit': float(total_profit_bot)
        }), 200
        
    except Exception as e:
        print(f"Erro Conversion Stats: {str(e)}")
        return jsonify({'error': 'Erro ao processar taxas de conversão'}), 500