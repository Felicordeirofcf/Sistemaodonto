from flask import Blueprint, jsonify, request
from app.models import db, InventoryItem, User
from flask_jwt_extended import jwt_required, get_jwt_identity

stock_bp = Blueprint('stock_bp', __name__)

# 1. LISTAR ESTOQUE
@stock_bp.route('/stock', methods=['GET'])
@jwt_required()
def get_stock():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Filtra pelo clinic_id
        items = InventoryItem.query.filter_by(clinic_id=user.clinic_id).order_by(InventoryItem.name).all()
        
        output = []
        for i in items:
            output.append({
                'id': i.id,
                'nome': i.name,
                'categoria': i.category,
                'quantidade': i.quantity,
                'minimo': i.min_quantity, # Campo correto no Model
                'preco_compra': i.purchase_price,
                'unidade': i.unit
            })
        return jsonify(output), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 2. CRIAR ITEM
@stock_bp.route('/stock', methods=['POST'])
@jwt_required()
def create_item():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        data = request.get_json()
        
        # Validação simples
        if not data.get('nome'):
            return jsonify({'error': 'Nome do item é obrigatório'}), 400

        new_item = InventoryItem(
            name=data.get('nome'),
            category=data.get('categoria', 'Material'),
            quantity=float(data.get('quantidade', 0)),
            min_quantity=float(data.get('minimo', 5)), # Campo correto
            purchase_price=float(data.get('preco_compra', 0)),
            unit=data.get('unidade', 'un'),
            clinic_id=user.clinic_id
        )

        db.session.add(new_item)
        db.session.commit()
        return jsonify({'message': 'Item criado com sucesso!', 'id': new_item.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro ao criar item', 'details': str(e)}), 500

# 3. ATUALIZAR QUANTIDADE
@stock_bp.route('/stock/<int:id>/update', methods=['PUT'])
@jwt_required()
def update_quantity(id):
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        item = InventoryItem.query.filter_by(id=id, clinic_id=user.clinic_id).first()
        
        if not item: 
            return jsonify({'error': 'Item não encontrado'}), 404
            
        data = request.get_json()
        delta = float(data.get('delta', 0))
        
        # Impede estoque negativo
        item.quantity = max(0, item.quantity + delta)
        
        db.session.commit()
        return jsonify({'message': 'Estoque atualizado', 'nova_qtd': item.quantity}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 4. DELETAR ITEM
@stock_bp.route('/stock/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_item(id):
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        item = InventoryItem.query.filter_by(id=id, clinic_id=user.clinic_id).first()
        
        if not item:
            return jsonify({'error': 'Item não encontrado'}), 404
            
        db.session.delete(item)
        db.session.commit()
        return jsonify({'message': 'Item removido do estoque'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500