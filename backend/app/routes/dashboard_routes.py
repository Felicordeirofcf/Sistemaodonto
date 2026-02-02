from flask import Blueprint, jsonify
from app import db
from app.models import Patient, InventoryItem, Transaction, User, Appointment
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, time

dashboard_bp = Blueprint('dashboard', __name__)

def resolve_user_and_clinic():
    """
    Suporta JWT identity como:
    - int/str: user_id
    - dict: {"id": user_id, "clinic_id": clinic_id}
    """
    identity = get_jwt_identity()

    # Caso identity venha como dict (mais robusto)
    if isinstance(identity, dict):
        user_id = identity.get("id") or identity.get("user_id")
        clinic_id = identity.get("clinic_id")
        return user_id, clinic_id

    # Caso identity venha como user_id puro
    return identity, None


@dashboard_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required()
def get_stats():
    try:
        user_id, clinic_id_from_token = resolve_user_and_clinic()

        user = None
        current_clinic_id = None

        # Se veio clinic_id no token, já usa (mais rápido)
        if clinic_id_from_token:
            current_clinic_id = int(clinic_id_from_token)
        else:
            # Senão, busca user no banco
            user = User.query.get(int(user_id)) if user_id is not None else None
            if not user:
                return jsonify({'error': 'Usuário não encontrado'}), 404
            current_clinic_id = user.clinic_id

        # Intervalo do dia (UTC)
        today_start = datetime.combine(datetime.utcnow().date(), time.min)
        today_end = datetime.combine(datetime.utcnow().date(), time.max)

        # 1. Pacientes Totais
        total_patients = Patient.query.filter_by(clinic_id=current_clinic_id).count() or 0

        # 2. Estoque Baixo ✅ CORRETO: min_stock (do seu model)
        low_stock_count = InventoryItem.query.filter(
            InventoryItem.clinic_id == current_clinic_id,
            InventoryItem.quantity <= db.func.coalesce(InventoryItem.min_stock, 0)
        ).count() or 0

        # 3. Financeiro do Dia
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
