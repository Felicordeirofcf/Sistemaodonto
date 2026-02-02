from flask import Blueprint, jsonify
from app.models import db, Patient, InventoryItem, Transaction, User, Appointment
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, time

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_stats():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
            
        current_clinic_id = user.clinic_id
        
        # 1. Pacientes Totais
        total_patients = Patient.query.filter_by(clinic_id=current_clinic_id).count() or 0
        
        # 2. Estoque Baixo (CORRIGIDO: min_quantity)
        # O erro estava aqui: InventoryItem.min_stock não existe mais
        low_stock_count = InventoryItem.query.filter(
            InventoryItem.clinic_id == current_clinic_id,
            InventoryItem.quantity <= db.func.coalesce(InventoryItem.min_quantity, 0)
        ).count() or 0
        
        # 3. Financeiro do Dia
        today_start = datetime.combine(datetime.utcnow().date(), time.min)
        today_end = datetime.combine(datetime.utcnow().date(), time.max)
        
        transacoes_hoje = Transaction.query.filter(
            Transaction.clinic_id == current_clinic_id,
            Transaction.date >= today_start,
            Transaction.date <= today_end
        ).all()
        
        faturamento_dia = sum(float(t.amount or 0.0) for t in transacoes_hoje if t.type == 'income')
        despesas_dia = sum(float(t.amount or 0.0) for t in transacoes_hoje if t.type == 'expense')
        lucro_dia = faturamento_dia - despesas_dia
        
        # 4. Consultas do dia
        agendamentos_hoje = Appointment.query.filter(
            Appointment.clinic_id == current_clinic_id,
            Appointment.date_time >= today_start,
            Appointment.date_time <= today_end
        ).count() or 0

        return jsonify({
            'patients': int(total_patients),
            'low_stock': int(low_stock_count),
            'revenue': float(faturamento_dia),
            'net_profit': float(lucro_dia),
            'appointments': int(agendamentos_hoje)
        }), 200

    except Exception as e:
        print(f"ERRO CRÍTICO DASHBOARD: {str(e)}")
        return jsonify({'error': 'Erro ao carregar indicadores'}), 500