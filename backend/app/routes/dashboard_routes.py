from flask import Blueprint, jsonify
from app.models import Patient, InventoryItem
from flask_jwt_extended import jwt_required, get_jwt

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard/stats', methods=['GET'])
@jwt_required() # <--- O CADEADO DE SEGURANÇA
def get_stats():
    # Pega os dados de dentro do Token (O crachá)
    claims = get_jwt()
    current_clinic_id = claims['clinic_id']
    
    # 1. Contar Pacientes da clínica certa
    total_patients = Patient.query.filter_by(clinic_id=current_clinic_id).count()
    
    # 2. Contar Estoque da clínica certa
    low_stock_count = InventoryItem.query.filter(
        InventoryItem.clinic_id == current_clinic_id,
        InventoryItem.quantity <= InventoryItem.min_quantity
    ).count()
    
    faturamento_dia = 4250.00 
    
    return jsonify({
        'patients': total_patients,
        'low_stock': low_stock_count,
        'revenue': faturamento_dia,
        'appointments': 5
    })