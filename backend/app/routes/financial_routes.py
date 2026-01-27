from flask import Blueprint, jsonify, request
from app.models import db, Transaction, User
from flask_jwt_extended import jwt_required, get_jwt_identity

financial_bp = Blueprint('financial_bp', __name__)

@financial_bp.route('/financial/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    user = User.query.get(get_jwt_identity())
    # Ordena por data (mais recente primeiro)
    transactions = Transaction.query.filter_by(clinic_id=user.clinic_id).order_by(Transaction.date.desc()).all()
    
    output = []
    total_balance = 0
    
    for t in transactions:
        total_balance += t.amount if t.type == 'income' else -t.amount
        output.append({
            'id': t.id,
            'description': t.description,
            'amount': t.amount,
            'type': t.type,
            'category': t.category,
            'date': t.date.isoformat()
        })
        
    return jsonify({'transactions': output, 'balance': total_balance}), 200