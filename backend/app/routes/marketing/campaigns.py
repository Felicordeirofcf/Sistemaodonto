from flask import Blueprint, request, jsonify, redirect, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Campaign, Lead, LeadEvent, WhatsAppConnection
import shortuuid
import qrcode
from io import BytesIO
import logging
import urllib.parse
import requests
import os

logger = logging.getLogger(__name__)

bp = Blueprint('marketing_campaigns', __name__)

# Configurações da API
EVOLUTION_API_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")

# ==============================================================================
# 1. GESTÃO DE CAMPANHAS
# ==============================================================================

@bp.route('/campaigns', methods=['POST'])
@jwt_required()
def create_campaign():
    identity = get_jwt_identity()
    clinic_id = identity.get('clinic_id') if isinstance(identity, dict) else 1
    data = request.get_json()
    
    code = shortuuid.ShortUUID().random(length=5)
    msg_template = data.get('message', "Olá, gostaria de saber mais.")
    if f"[ref:{code}]" not in msg_template:
        msg_template += f" [ref:{code}]"

    new_campaign = Campaign(
        clinic_id=clinic_id,
        name=data['name'],
        slug=data.get('slug'), 
        tracking_code=code,
        whatsapp_message_template=msg_template,
        landing_page_data=data.get('landing_data', {}),
        active=True
    )
    
    db.session.add(new_campaign)
    db.session.commit()
    
    base_url = request.host_url.rstrip('/')
    return jsonify({
        "id": new_campaign.id,
        "name": new_campaign.name,
        "tracking_code": code,
        "tracking_url": f"{base_url}/c/{code}",
        "active": True,
        "clicks": 0, 
        "leads": 0
    }), 201

@bp.route('/campaigns', methods=['GET'])
@jwt_required()
def list_campaigns():
    identity = get_jwt_identity()
    clinic_id = identity.get('clinic_id') if isinstance(identity, dict) else 1
    
    campaigns = Campaign.query.filter_by(clinic_id=clinic_id).order_by(Campaign.created_at.desc()).all()
    base_url = request.host_url.rstrip('/')
    
    return jsonify([{
        "id": c.id,
        "name": c.name,
        "tracking_code": c.tracking_code,
        "tracking_url": f"{base_url}/c/{c.tracking_code}",
        "active": c.active,
        "clicks": c.clicks_count,
        "leads": c.leads_count,
        "qr_code_url": f"{base_url}/api/marketing/campaigns/{c.id}/qr"
    } for c in campaigns]), 200

@bp.route('/campaigns/<int:id>/status', methods=['PATCH'])
@jwt_required()
def toggle_status(id):
    identity = get_jwt_identity()
    clinic_id = identity.get('clinic_id') if isinstance(identity, dict) else 1
    camp = Campaign.query.filter_by(id=id, clinic_id=clinic_id).first_or_404()
    
    data = request.get_json()
    if 'active' in data:
        camp.active = bool(data['active'])
        db.session.commit()
    return jsonify({"message": "Status atualizado", "active": camp.active}), 200

@bp.route('/campaigns/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_campaign(id):
    identity = get_jwt_identity()
    clinic_id = identity.get('clinic_id') if isinstance(identity, dict) else 1
    camp = Campaign.query.filter_by(id=id, clinic_id=clinic_id).first_or_404()
    
    try:
        LeadEvent.query.filter_by(campaign_id=id).delete()
        leads = Lead.query.filter_by(campaign_id=id).all()
        for lead in leads: lead.campaign_id = None
        db.session.delete(camp)
        db.session.commit()
        return jsonify({"message": "Campanha excluída"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ==============================================================================
# 2. ROTA DE RASTREAMENTO (CORRIGIDA)
# ==============================================================================
@bp.route('/c/<code>', methods=['GET'])
def track_click_and_redirect(code):
    campaign = Campaign.query.filter_by(tracking_code=code).first()
    
    if not campaign:
        return "<h1 style='font-family:sans-serif;text-align:center;margin-top:50px;'>⚠️ Link Inválido ou Não Encontrado</h1>", 404

    if not campaign.active:
        return "<h1 style='font-family:sans-serif;text-align:center;margin-top:50px;'>⏸️ Campanha Pausada</h1>", 200
    
    # 1. Registra o Clique
    try:
        campaign.clicks_count += 1
        event = LeadEvent(
            campaign_id=campaign.id, 
            event_type='click',
            metadata_json={'user_agent': request.headers.get('User-Agent')}
        )
        db.session.add(event)
        db.session.commit()
    except Exception as e:
        print(f"Erro ao salvar métrica: {e}")

    # 2. Descobre o Número (Lógica Blindada)
    target_phone = None
    
    # Tenta conexão do banco
    conn = WhatsAppConnection.query.filter_by(clinic_id=campaign.clinic_id).first()
    
    # A) Tenta cache do banco
    if conn and conn.session_data:
        jid = conn.session_data.get('me', {}).get('id')
        if jid:
            target_phone = jid.split('@')[0].split(':')[0]

    # B) Tenta API Evolution (Se não achou no banco)
    if not target_phone:
        print(f"🔄 [API] Buscando instâncias na Evolution...")
        try:
            url = f"{EVOLUTION_API_URL}/instance/fetchInstances"
            headers = {"apikey": EVOLUTION_API_KEY}
            resp = requests.get(url, headers=headers, timeout=5)
            
            if resp.status_code == 200:
                instances = resp.json()
                # Pega a PRIMEIRA instância que estiver conectada (status: open)
                active_instance = next((i for i in instances if i.get('instance', {}).get('status') == 'open'), None)
                
                if active_instance:
                    owner_jid = active_instance['instance']['owner'] # ex: 5511999999@s.whatsapp.net
                    target_phone = owner_jid.split('@')[0].split(':')[0]
                    print(f"✅ [API] Instância encontrada: {active_instance['instance']['instanceName']} -> {target_phone}")
                    
                    # Salva no banco para ficar rápido na próxima
                    if conn:
                        conn.session_data = {"me": {"id": owner_jid}}
                        conn.status = "connected"
                        db.session.commit()
        except Exception as e:
            print(f"❌ Erro ao consultar Evolution API: {e}")

    # C) Fallback Final (Se tudo falhar, usa um padrão ou erro)
    if not target_phone:
         return """
        <div style="font-family:sans-serif; text-align:center; padding:50px;">
            <h1>⚠️ WhatsApp Não Conectado</h1>
            <p>Não foi possível identificar o número da clínica.</p>
            <p>Verifique se o QR Code está conectado no painel.</p>
        </div>
        """, 503

    # 3. Redireciona
    text_encoded = urllib.parse.quote(campaign.whatsapp_message_template)
    whatsapp_url = f"https://api.whatsapp.com/send?phone={target_phone}&text={text_encoded}"
    
    return redirect(whatsapp_url)

# ==============================================================================
# 3. QR CODE
# ==============================================================================
@bp.route('/campaigns/<int:campaign_id>/qr', methods=['GET'])
def get_qr_code(campaign_id):
    camp = Campaign.query.get_or_404(campaign_id)
    base_url = request.host_url.rstrip('/')
    link = f"{base_url}/c/{camp.tracking_code}"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')