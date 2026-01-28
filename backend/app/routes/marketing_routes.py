from flask import Blueprint, jsonify, request
from app.models import db, Lead, User, Patient, Appointment, MarketingCampaign, Clinic
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

# Unificando o nome do blueprint para o padrão que usamos no __init__.py
marketing_bp = Blueprint('marketing', __name__)

# --- 1. GESTÃO DE LEADS (KANBAN) ---

@marketing_bp.route('/marketing/leads', methods=['GET'])
@jwt_required()
def get_leads():
    try:
        user = User.query.get(get_jwt_identity())
        # Busca leads garantindo isolamento por clínica
        leads = Lead.query.filter_by(clinic_id=user.clinic_id).all()
        return jsonify([lead.to_dict() for lead in leads]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@marketing_bp.route('/marketing/leads', methods=['POST'])
@jwt_required()
def create_lead():
    try:
        user = User.query.get(get_jwt_identity())
        data = request.get_json()
        
        new_lead = Lead(
            clinic_id=user.clinic_id,
            name=data.get('name'),
            phone=data.get('phone'),
            source=data.get('source', 'Manual'),
            status='new', # Status inicial do funil
            notes=data.get('notes', '')
        )
        db.session.add(new_lead)
        db.session.commit()
        return jsonify(new_lead.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro ao criar lead'}), 500

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
    return jsonify({'message': 'Lead movido com sucesso!'}), 200

# --- 2. AUTOMAÇÃO DE ADS (IA DE CRESCIMENTO) ---
# Esta rota atende ao botão "Iniciar Crescimento" do frontend

@marketing_bp.route('/marketing/campaign/activate', methods=['POST'])
@jwt_required()
def activate_ads():
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)
        data = request.get_json()
        
        budget = float(data.get('budget', 300))
        
        # Cria ou atualiza a campanha ativa
        campaign = MarketingCampaign.query.filter_by(clinic_id=clinic.id, status='active').first()
        
        if not campaign:
            campaign = MarketingCampaign(
                clinic_id=clinic.id,
                name=f"Crescimento Automático - {clinic.name}",
                budget=budget,
                daily_spend=budget / 30, # Gasto diário automático
                status='active'
            )
            db.session.add(campaign)
        else:
            campaign.budget = budget
            campaign.daily_spend = budget / 30

        db.session.commit()
        return jsonify({'message': 'Campanha ativada!', 'daily_spend': round(campaign.daily_spend, 2)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# --- 3. REATIVAÇÃO (ROBÔ DE PACIENTES SUMIDOS) ---

@marketing_bp.route('/marketing/campaign/recall', methods=['GET'])
@jwt_required()
def get_recall_campaign():
    user = User.query.get(get_jwt_identity())
    
    # Critério: 6 meses sem visita
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    
    candidates = Patient.query.filter(
        Patient.clinic_id == user.clinic_id,
        Patient.last_visit <= six_months_ago
    ).all()

    # Verifica ocupação para sugerir horários amanhã
    amanha = datetime.utcnow().date() + timedelta(days=1)
    agendamentos_amanha = Appointment.query.filter(
        Appointment.clinic_id == user.clinic_id,
        db.func.date(Appointment.date_time) == amanha
    ).count() # Usando count() para ser mais leve
    
    has_slots = agendamentos_amanha < 8 

    output = []
    for p in candidates:
        last_visit_str = p.last_visit.strftime('%d/%m/%Y') if p.last_visit else "Não registrada"
        
        # Mensagem dinâmica para a secretária apenas clicar e enviar
        msg = f"Olá {p.name}! O Dr. notou que sua última revisão foi em {last_visit_str}. "
        msg += "Temos horários livres para amanhã, vamos agendar?" if has_slots else "Que tal agendar sua limpeza preventiva?"

        output.append({
            'id': p.id,
            'name': p.name,
            'phone': p.phone,
            'last_visit': last_visit_str,
            'suggested_msg': msg
        })
    
    return jsonify(output), 200