from flask import Blueprint, jsonify, request
from app.models import db, Transaction, User
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

financial_bp = Blueprint('financial_bp', __name__)

# 1. OBTER RESUMO FINANCEIRO (DASHBOARD)
@financial_bp.route('/financial/summary', methods=['GET'])
@jwt_required()
def get_financial_summary():
    user = User.query.get(get_jwt_identity())
    transactions = Transaction.query.filter_by(clinic_id=user.clinic_id).all()
    
    total_receita = sum(t.amount for t in transactions if t.type == 'income')
    total_despesas = sum(t.amount for t in transactions if t.type == 'expense')
    lucro = total_receita - total_despesas
    
    # Pegar as últimas 20 transações
    recent_transactions = []
    for t in sorted(transactions, key=lambda x: x.date, reverse=True)[:20]:
        recent_transactions.append({
            'id': t.id,
            'description': t.description,
            'amount': t.amount,
            'type': t.type,
            'category': t.category,
            'date': t.date.isoformat()
        })

    return jsonify({
        'receita': total_receita,
        'despesas': total_despesas,
        'lucro': lucro,
        'transactions': recent_transactions
    }), 200

# 2. LANÇAR DESPESA MANUAL (Aluguel, Luz, Compras)
@financial_bp.route('/financial/expense', methods=['POST'])
@jwt_required()
def add_expense():
    user = User.query.get(get_jwt_identity())
    data = request.get_json()
    
    new_expense = Transaction(
        clinic_id=user.clinic_id,
        description=data['description'], # Ex: "Conta de Luz"
        amount=float(data['amount']),
        type='expense',
        category=data.get('category', 'Despesa Fixa'),
        date=datetime.utcnow()
    )
    
    db.session.add(new_expense)
    db.session.commit()
    
    return jsonify({'message': 'Despesa lançada com sucesso!'}), 201