from flask import Blueprint, request, jsonify, redirect, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Campaign, Lead, LeadEvent, LeadStatus, WhatsAppConnection
import shortuuid
import qrcode
from io import BytesIO
import logging

# Configuração de Logs
logger = logging.getLogger(__name__)

bp = Blueprint('marketing_campaigns', __name__)

# ==============================================================================
# 1. GESTÃO DE CAMPANHAS (CRIAR & LISTAR)
# ==============================================================================

@bp.route('/campaigns', methods=['POST'])
@jwt_required()
def create_campaign():
    identity = get_jwt_identity()
    clinic_id = identity.get('clinic_id') if isinstance(identity, dict) else 1
    
    data = request.get_json()
    
    # Gera código único de 5 caracteres
    code = shortuuid.ShortUUID().random(length=5)
    
    # Garante o token [ref:CODE] na mensagem
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
    
    # Monta URLs absolutas
    base_url = request.host_url.rstrip('/')
    
    logger.info(f"✅ Campanha Criada: {new_campaign.name} | Code: {code}")
    
    return jsonify({
        "id": new_campaign.id,
        "name": new_campaign.name,
        "tracking_code": code,
        "tracking_url": f"{base_url}/c/{code}",
        "qr_code_url": f"{base_url}/api/marketing/campaigns/{new_campaign.id}/qr",
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
        "clicks": c.clicks_count,
        "leads": c.leads_count
    } for c in campaigns]), 200

# ==============================================================================
# 2. ROTA DE RASTREAMENTO (O "PULO DO GATO")
# ==============================================================================
@bp.route('/c/<code>', methods=['GET'])
def track_click_and_redirect(code):
    print(f"🔎 [DEBUG] Tentando acessar campanha com código: {code}")
    
    # Busca a campanha (sem 404 automático para podermos tratar o erro)
    campaign = Campaign.query.filter_by(tracking_code=code).first()
    
    if not campaign:
        print(f"❌ [ERRO] Campanha {code} não encontrada no banco!")
        # Retorna erro visível em vez de redirecionar para Home
        return f"""
        <div style="font-family:sans-serif; text-align:center; padding:50px;">
            <h1>⚠️ Link Inválido ou Expirado</h1>
            <p>Não encontramos a campanha com código: <strong>{code}</strong></p>
            <p>Verifique se ela foi criada corretamente no painel.</p>
        </div>
        """, 404
    
    # 1. Registra Métrica
    try:
        campaign.clicks_count += 1
        event = LeadEvent(
            campaign_id=campaign.id,
            event_type='click',
            metadata_json={
                'user_agent': request.headers.get('User-Agent'),
                'ip': request.remote_addr
            }
        )
        db.session.add(event)
        db.session.commit()
    except Exception as e:
        print(f"⚠️ Erro ao salvar métrica (mas vamos redirecionar): {e}")

    # 2. Descobre o número do WhatsApp da Clínica
    # Tenta buscar conexão "connected" ou "CONNECTED"
    target_phone = "5511999999999" # Fallback
    
    try:
        connection = WhatsAppConnection.query.filter(
            WhatsAppConnection.clinic_id == campaign.clinic_id,
            WhatsAppConnection.status.in_(['connected', 'CONNECTED'])
        ).first()
        
        if connection and connection.session_data:
            # Tenta pegar do session_data, ex: "551199999@s.whatsapp.net"
            jid = connection.session_data.get('me', {}).get('id')
            if jid:
                target_phone = jid.split('@')[0]
                print(f"✅ Redirecionando para WhatsApp da Clínica: {target_phone}")
    except Exception as e:
        print(f"⚠️ Erro ao buscar conexão: {e}")

    # 3. Redireciona
    import urllib.parse
    text_encoded = urllib.parse.quote(campaign.whatsapp_message_template)
    whatsapp_url = f"https://wa.me/{target_phone}?text={text_encoded}"
    
    return redirect(whatsapp_url)

# ==============================================================================
# 3. GERADOR DE QR CODE
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