from flask import Blueprint, jsonify, request
from app.models import db, InventoryItem, User
from flask_jwt_extended import jwt_required, get_jwt_identity

stock_bp = Blueprint('stock_bp', __name__)

@stock_bp.route('/stock', methods=['GET'])
@jwt_required()
def get_stock():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    items = InventoryItem.query.filter_by(clinic_id=user.clinic_id).all()
    
    output = []
    for i in items:
        output.append({
            'id': i.id,
            'nome': i.name,
            'categoria': i.category,
            'quantidade': i.quantity,
            'minimo': i.min_quantity, # <--- Importante
            'unidade': i.unit
        })
    return jsonify(output), 200

@stock_bp.route('/stock', methods=['POST'])
@jwt_required()
def create_item():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    data = request.get_json()
    
    new_item = InventoryItem(
        name=data.get('nome'),
        category=data.get('categoria', 'Material'),
        quantity=int(data.get('quantidade', 0)),
        min_quantity=int(data.get('minimo', 5)), # <--- CORREÇÃO: Mapeia 'minimo' para 'min_quantity'
        unit=data.get('unidade', 'un'),
        clinic_id=user.clinic_id
    )

    try:
        db.session.add(new_item)
        db.session.commit()
        return jsonify({'message': 'Item criado com sucesso!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro ao criar item', 'details': str(e)}), 500

@stock_bp.route('/stock/<int:id>/update', methods=['PUT'])
@jwt_required()
def update_quantity(id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    item = InventoryItem.query.filter_by(id=id, clinic_id=user.clinic_id).first()
    
    if not item: return jsonify({'error': 'Item não encontrado'}), 404
        
    data = request.get_json()
    item.quantity = max(0, item.quantity + data.get('delta', 0))
    db.session.commit()
    return jsonify({'message': 'Estoque atualizado'}), 200