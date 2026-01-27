from flask import Blueprint, request, jsonify
from app.models import InventoryItem, db
from flask_jwt_extended import jwt_required, get_jwt

stock_bp = Blueprint('stock', __name__)

@stock_bp.route('/stock', methods=['GET'])
@jwt_required()
def get_stock():
    claims = get_jwt()
    current_clinic_id = claims['clinic_id']
    
    items = InventoryItem.query.filter_by(clinic_id=current_clinic_id).all()
    
    output = []
    for i in items:
        output.append({
            'id': i.id,
            'nome': i.name,
            'categoria': i.category,
            'quantidade': i.quantity,
            'minimo': i.min_quantity,
            'unidade': i.unit
        })
    return jsonify(output), 200

@stock_bp.route('/stock', methods=['POST'])
@jwt_required()
def create_item():
    claims = get_jwt()
    current_clinic_id = claims['clinic_id']
    data = request.get_json()
    
    new_item = InventoryItem(
        name=data['nome'],
        category=data.get('categoria', 'Geral'),
        quantity=int(data.get('quantidade', 0)),
        minimo=int(data.get('minimo', 5)), # Nota: verifique se seu modelo usa min_quantity ou minimo. Vou usar min_quantity baseado no modelo anterior.
        unit=data.get('unidade', 'un'),
        clinic_id=current_clinic_id # ID DO TOKEN
    )
    # Correção do nome do campo se necessário (baseado no models.py anterior era min_quantity)
    new_item.min_quantity = int(data.get('minimo', 5))

    db.session.add(new_item)
    db.session.commit()
    return jsonify({'message': 'Item criado!'}), 201

@stock_bp.route('/stock/<int:id>/update', methods=['PUT'])
@jwt_required()
def update_quantity(id):
    claims = get_jwt()
    current_clinic_id = claims['clinic_id']
    
    # Filtra pelo ID do item E pela clínica (segurança dupla)
    item = InventoryItem.query.filter_by(id=id, clinic_id=current_clinic_id).first()
    
    if not item:
        return jsonify({'error': 'Item não encontrado'}), 404
        
    delta = request.get_json().get('delta', 0)
    item.quantity = max(0, item.quantity + delta)
    db.session.commit()
    
    return jsonify({'message': 'Atualizado', 'nova_quantidade': item.quantity}), 200