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
    
    # Filtra apenas transações da clínica do usuário logado
    transactions = Transaction.query.filter_by(clinic_id=user.clinic_id).all()
    
    total_receita = sum(t.amount for t in transactions if t.type == 'income')
    total_despesas = sum(t.amount for t in transactions if t.type == 'expense')
    lucro = total_receita - total_despesas
    
    # Pegar as últimas 20 transações para a tabela
    recent_transactions = []
    for t in sorted(transactions, key=lambda x: x.date, reverse=True)[:20]:
        recent_transactions.append({
            'id': t.id,
            'description': t.description,
            'amount': t.amount,
            'type': t.type,
            'category': t.category,
            'date': t.date.strftime('%Y-%m-%d')  # Formatado para string legível
        })

    return jsonify({
        'receita': total_receita,
        'despesas': total_despesas,
        'lucro': lucro,
        'transactions': recent_transactions
    }), 200

# 2. LANÇAR TRANSAÇÃO (Receita ou Despesa)
# CORREÇÃO: A rota agora bate com o que o Frontend chama (/financial/transaction)
@financial_bp.route('/financial/transaction', methods=['POST'])
@jwt_required()
def add_transaction():
    try:
        user = User.query.get(get_jwt_identity())
        data = request.get_json()
        
        # Validação básica
        if not data.get('description') or not data.get('amount'):
            return jsonify({'error': 'Descrição e valor são obrigatórios'}), 400

        # Define o tipo (income ou expense). Se não vier, assume expense.
        trans_type = data.get('type', 'expense') 

        new_transaction = Transaction(
            clinic_id=user.clinic_id,
            description=data['description'],
            amount=float(data['amount']),
            type=trans_type, 
            category=data.get('category', 'Geral'),
            date=datetime.utcnow()
        )
        
        db.session.add(new_transaction)
        db.session.commit()
        
        return jsonify({'message': 'Transação salva com sucesso!', 'id': new_transaction.id}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao salvar: {str(e)}'}), 500