from flask import Blueprint, jsonify, request
from app.models import db, Procedure, ProcedureRequirement, InventoryItem, User
from flask_jwt_extended import jwt_required, get_jwt_identity

procedure_bp = Blueprint('procedure_bp', __name__)

# 1. LISTAR PROCEDIMENTOS E SEUS INSUMOS
@procedure_bp.route('/procedures', methods=['GET'])
@jwt_required()
def get_procedures():
    user = User.query.get(get_jwt_identity())
    # Garante que filtre apenas pela clínica do usuário logado
    procedures = Procedure.query.filter_by(clinic_id=user.clinic_id).all()
    
    output = []
    for p in procedures:
        output.append({
            'id': p.id,
            'name': p.name,
            'price': float(p.price or 0), # Evita erro de undefined no front
            'items': [{
                'name': req.item.name,
                'quantity': req.quantity_needed,
                'unit': req.item.unit
            } for req in p.requirements]
        })
    return jsonify(output), 200

# 2. CADASTRAR PROCEDIMENTO COM INSUMOS (CORRIGIDO: ACEITA POST)
@procedure_bp.route('/procedures', methods=['POST'])
@jwt_required()
def create_procedure():
    try:
        user = User.query.get(get_jwt_identity())
        data = request.get_json()
        
        # Validação básica para evitar erros 500
        if not data.get('name') or not data.get('price'):
            return jsonify({'error': 'Nome e preço são obrigatórios'}), 400
            
        new_proc = Procedure(
            name=data['name'],
            price=data['price'],
            clinic_id=user.clinic_id
        )
        db.session.add(new_proc)
        db.session.flush() # Gera o ID para as FKs de requerimentos

        # Vincula os itens do estoque ao procedimento
        if 'items' in data and isinstance(data['items'], list):
            for item in data['items']:
                req = ProcedureRequirement(
                    procedure_id=new_proc.id,
                    inventory_item_id=item['inventory_item_id'],
                    quantity_needed=item['quantity']
                )
                db.session.add(req)
        
        db.session.commit()
        return jsonify({'message': 'Procedimento e insumos configurados!'}), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar procedimento: {str(e)}")
        return jsonify({'error': 'Erro interno ao salvar'}), 500

# 3. ROTA AUXILIAR PARA O FRONTEND BUSCAR OS INSUMOS DISPONÍVEIS
@procedure_bp.route('/inventory/options', methods=['GET'])
@jwt_required()
def get_inventory_options():
    user = User.query.get(get_jwt_identity())
    # Necessário para que o select do Frontend pare de ficar em branco
    items = InventoryItem.query.filter_by(clinic_id=user.clinic_id).all()
    return jsonify([{
        'id': i.id,
        'name': i.name,
        'unit': i.unit
    } for i in items]), 200