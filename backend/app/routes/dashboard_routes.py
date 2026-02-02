from flask import Blueprint, jsonify
from app.models import db, Patient, InventoryItem, Transaction, User, Appointment
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_stats():
    try:
        # Busca segura do usuário para garantir a clínica correta pós-reset
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
            
        current_clinic_id = user.clinic_id
        
        # 1. Estatísticas Básicas
        total_patients = Patient.query.filter_by(clinic_id=current_clinic_id).count() or 0
        
        # Coalesce garante que se min_stock for NULL, ele use 0 para a comparação
        low_stock_count = InventoryItem.query.filter(
            InventoryItem.clinic_id == current_clinic_id,
            InventoryItem.quantity <= db.func.coalesce(InventoryItem.min_stock, 0)
        ).count() or 0
        
        # 2. Financeiro do Dia
        hoje = datetime.utcnow().date()
        transacoes_hoje = Transaction.query.filter(
            Transaction.clinic_id == current_clinic_id,
            db.func.date(Transaction.date) == hoje
        ).all()
        
        # Somas seguras tratando explicitamente tipos para o Frontend
        faturamento_dia = sum(float(t.amount or 0.0) for t in transacoes_hoje if t.type == 'income')
        
        # Nota: 'cost' não existe no modelo Transaction simplificado, removendo cálculo de lucro baseado em cost
        # Se o usuário quiser lucro, precisaria de uma lógica de despesas (type == 'expense')
        despesas_dia = sum(float(t.amount or 0.0) for t in transacoes_hoje if t.type == 'expense')
        lucro_dia = faturamento_dia - despesas_dia
        
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
