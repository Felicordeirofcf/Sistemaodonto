from flask import Blueprint, request, jsonify, redirect
from app.models import db, Campaign, Lead, LeadEvent, LeadStatus
import shortuuid # Sugestão: pip install shortuuid para gerar códigos curtos

marketing_bp = Blueprint('marketing', __name__)

@marketing_bp.route('/api/v1/marketing/campaigns', methods=['POST'])
# @jwt_required()  <-- Adicione sua autenticação aqui
def create_campaign():
    data = request.json
    # Gera código único curto (ex: 3k9z)
    code = shortuuid.ShortUUID().random(length=5)
    
    new_campaign = Campaign(
        clinic_id=data['clinic_id'], # Pegar do token JWT idealmente
        name=data['name'],
        slug=data.get('slug'), # Opcional
        tracking_code=code,
        whatsapp_message_template=data.get('message', f"Olá, gostaria de saber mais. [ref:{code}]"),
        landing_page_data=data.get('landing_data', {})
    )
    db.session.add(new_campaign)
    db.session.commit()
    
    return jsonify({
        "id": new_campaign.id,
        "tracking_url": f"https://seusistema.com/c/{code}",
        "qr_code_endpoint": f"/api/v1/marketing/campaigns/{new_campaign.id}/qr"
    }), 201

@marketing_bp.route('/api/v1/marketing/metrics', methods=['GET'])
def get_metrics():
    # Retorna JSON para montar dashboard sem mudar UI
    campaign_id = request.args.get('campaignId')
    camp = Campaign.query.get(campaign_id)
    return jsonify({
        "clicks": camp.clicks_count,
        "leads": camp.leads_count,
        "leads_by_status": {
            "new": Lead.query.filter_by(campaign_id=campaign_id, status='novo').count(),
            "converted": Lead.query.filter_by(campaign_id=campaign_id, status='convertido').count(),
        }
    })