from flask import Blueprint, jsonify, request
from app.models import db, Procedure, ProcedureRequirement, InventoryItem, User
from flask_jwt_extended import jwt_required, get_jwt_identity

procedure_bp = Blueprint('procedure_bp', __name__)

# 1. LISTAR PROCEDIMENTOS E SEUS INSUMOS
@procedure_bp.route('/procedures', methods=['GET'])
@jwt_required()
def get_procedures():
    user = User.query.get(get_jwt_identity())
    procedures = Procedure.query.filter_by(clinic_id=user.clinic_id).all()
    
    output = []
    for p in procedures:
        output.append({
            'id': p.id,
            'name': p.name,
            'price': p.price,
            'items': [{
                'name': req.item.name,
                'quantity': req.quantity_needed,
                'unit': req.item.unit
            } for req in p.requirements]
        })
    return jsonify(output), 200

# 2. CADASTRAR PROCEDIMENTO COM INSUMOS
@procedure_bp.route('/procedures', methods=['POST'])
@jwt_required()
def create_procedure():
    user = User.query.get(get_jwt_identity())
    data = request.get_json()
    
    new_proc = Procedure(
        name=data['name'],
        price=data['price'],
        clinic_id=user.clinic_id
    )
    db.session.add(new_proc)
    db.session.flush() # Para pegar o ID do novo procedimento

    # Vincula os itens do estoque ao procedimento
    for item in data['items']:
        req = ProcedureRequirement(
            procedure_id=new_proc.id,
            inventory_item_id=item['inventory_item_id'],
            quantity_needed=item['quantity']
        )
        db.session.add(req)
    
    db.session.commit()
    return jsonify({'message': 'Procedimento e insumos configurados!'}), 201