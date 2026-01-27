from flask import Blueprint, jsonify, request
from app.models import db, Lead, User, Patient, Appointment
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

marketing_bp = Blueprint('marketing_bp', __name__)

# --- ROTAS DE LEADS (KANBAN) ---

@marketing_bp.route('/marketing/leads', methods=['GET'])
@jwt_required()
def get_leads():
    user = User.query.get(get_jwt_identity())
    leads = Lead.query.filter_by(clinic_id=user.clinic_id).all()
    return jsonify([lead.to_dict() for lead in leads]), 200

@marketing_bp.route('/marketing/leads', methods=['POST'])
@jwt_required()
def create_lead():
    user = User.query.get(get_jwt_identity())
    data = request.get_json()
    new_lead = Lead(
        clinic_id=user.clinic_id,
        name=data.get('name'),
        phone=data.get('phone'),
        source=data.get('source', 'Manual'),
        status='new',
        notes=data.get('notes', '')
    )
    db.session.add(new_lead)
    db.session.commit()
    return jsonify(new_lead.to_dict()), 201

@marketing_bp.route('/marketing/leads/<int:id>/move', methods=['PUT'])
@jwt_required()
def move_lead(id):
    user = User.query.get(get_jwt_identity())
    data = request.get_json()
    lead = Lead.query.filter_by(id=id, clinic_id=user.clinic_id).first()
    if not lead:
        return jsonify({'error': 'Lead não encontrado'}), 404
    lead.status = data.get('status')
    db.session.commit()
    return jsonify({'message': 'Status atualizado!'}), 200

# --- NOVO: IA DE REATIVAÇÃO & LINK COM AGENDA ---

@marketing_bp.route('/marketing/campaign/recall-candidates', methods=['GET'])
@jwt_required()
def get_recall_candidates():
    user = User.query.get(get_jwt_identity())
    # Filtro: Pacientes que não vêm há mais de 6 meses
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    
    # Busca pacientes "sumidos"
    candidates = Patient.query.filter(
        Patient.clinic_id == user.clinic_id,
        Patient.last_visit <= six_months_ago
    ).all()

    # Busca horários LIVRES na agenda para amanhã (Exemplo de link com agenda)
    # Aqui o robô olha onde tem buraco na agenda do médico
    amanha = datetime.utcnow().date() + timedelta(days=1)
    agendamentos_amanha = Appointment.query.filter(
        Appointment.clinic_id == user.clinic_id,
        db.func.date(Appointment.date_time) == amanha
    ).all()
    
    # Lógica simples: Se tem menos de 5 agendamentos, sugere que há vagas
    has_slots = len(agendamentos_amanha) < 8 

    output = []
    for p in candidates:
        output.append({
            'id': p.id,
            'name': p.name,
            'phone': p.phone,
            'last_visit': p.last_visit.strftime('%d/%m/%Y') if p.last_visit else "Nunca",
            'suggested_msg': f"Olá {p.name}! Notamos que sua última revisão foi em {p.last_visit.year if p.last_visit else 'algum tempo'}. O Dr. tem horários disponíveis para amanhã. Vamos garantir sua saúde bucal?" if has_slots else f"Olá {p.name}, que tal agendarmos sua limpeza preventiva?"
        })
    
    return jsonify(output), 200