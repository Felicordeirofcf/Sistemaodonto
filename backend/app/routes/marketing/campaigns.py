from flask import Blueprint, request, jsonify, redirect, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Campaign, Lead, LeadEvent, LeadStatus, WhatsAppConnection
import shortuuid  # pip install shortuuid
import qrcode     # pip install qrcode[pil]
from io import BytesIO
from datetime import datetime

bp = Blueprint('marketing_campaigns', __name__)

# ==============================================================================
# 1. GESTÃO DE CAMPANHAS (CRIAR & METRICAS)
# ==============================================================================

@bp.route('/campaigns', methods=['POST'])
@jwt_required()
def create_campaign():
    identity = get_jwt_identity()
    # Garante que pega o clinic_id do token (segurança) ou fallback para 1 em dev
    clinic_id = identity.get('clinic_id') if isinstance(identity, dict) else 1
    
    data = request.get_json()
    
    # Gera código único curto (ex: 3k9z) para rastreio
    code = shortuuid.ShortUUID().random(length=5)
    
    # Monta a mensagem padrão com o "Token Mágico" [ref:CODE]
    # Esse token é o que permite o Webhook saber de qual campanha veio o lead
    msg_template = data.get('message', "Olá, gostaria de saber mais sobre a promoção.")
    if f"[ref:{code}]" not in msg_template:
        msg_template += f" [ref:{code}]"

    new_campaign = Campaign(
        clinic_id=clinic_id,
        name=data['name'],
        slug=data.get('slug'), # Opcional (para Landing Page)
        tracking_code=code,
        whatsapp_message_template=msg_template,
        landing_page_data=data.get('landing_data', {}),
        active=True
    )
    
    db.session.add(new_campaign)
    db.session.commit()
    
    # Gera URLs dinâmicas baseadas no domínio atual
    base_url = request.host_url.rstrip('/')
    tracking_url = f"{base_url}/c/{code}"
    
    return jsonify({
        "id": new_campaign.id,
        "name": new_campaign.name,
        "tracking_code": code,
        "tracking_url": tracking_url,
        "qr_code_url": f"{base_url}/api/marketing/campaigns/{new_campaign.id}/qr"
    }), 201

@bp.route('/metrics', methods=['GET'])
@jwt_required()
def get_metrics():
    clinic_id = get_jwt_identity().get('clinic_id') if isinstance(get_jwt_identity(), dict) else 1
    campaign_id = request.args.get('campaignId')
    
    if not campaign_id:
        return jsonify({"error": "campaignId é obrigatório"}), 400
        
    camp = Campaign.query.filter_by(id=campaign_id, clinic_id=clinic_id).first_or_404()
    
    return jsonify({
        "campaign": camp.name,
        "clicks": camp.clicks_count,
        "leads": camp.leads_count,
        "leads_by_status": {
            "new": Lead.query.filter_by(campaign_id=camp.id, status=LeadStatus.NEW).count(),
            "in_chat": Lead.query.filter_by(campaign_id=camp.id, status=LeadStatus.IN_CHAT).count(),
            "converted": Lead.query.filter_by(campaign_id=camp.id, status=LeadStatus.CONVERTED).count(),
        }
    })

# ==============================================================================
# 2. ROTA DE RASTREAMENTO (O "PULO DO GATO")
# ==============================================================================
# Esta rota deve ser registrada na raiz ou acessível publicamente (/c/CODIGO)
# Ela registra o clique e redireciona para o WhatsApp

@bp.route('/c/<code>', methods=['GET'])
def track_click_and_redirect(code):
    campaign = Campaign.query.filter_by(tracking_code=code).first_or_404()
    
    # 1. Registra Métrica (Incrementa contador e loga evento)
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
    
    # 2. Descobre o número do WhatsApp da Clínica para redirecionar
    # Tenta pegar da conexão ativa ou usa um fallback
    connection = WhatsAppConnection.query.filter_by(clinic_id=campaign.clinic_id, status='CONNECTED').first()
    
    # Se não tiver conexão ativa, usa um número padrão ou do cadastro da clínica
    # Aqui estou colocando um número fictício, você deve ajustar para pegar do model Clinic
    target_phone = "5511999999999" 
    if connection and connection.session_data:
        # Tenta extrair o número da sessão se disponível, ou usa o configurado
        target_phone = connection.session_data.get('me', {}).get('id', '').split('@')[0] or target_phone

    # 3. Monta URL do WhatsApp
    # Codifica a mensagem para URL
    import urllib.parse
    text_encoded = urllib.parse.quote(campaign.whatsapp_message_template)
    
    whatsapp_url = f"https://wa.me/{target_phone}?text={text_encoded}"
    
    return redirect(whatsapp_url)

# ==============================================================================
# 3. GERADOR DE QR CODE
# ==============================================================================

@bp.route('/campaigns/<int:campaign_id>/qr', methods=['GET'])
def get_qr_code(campaign_id):
    # Nota: Rota pública para carregar em e-mails/impressos, ou proteja se preferir
    camp = Campaign.query.get_or_404(campaign_id)
    
    base_url = request.host_url.rstrip('/')
    link = f"{base_url}/c/{camp.tracking_code}"
    
    # Gera imagem na memória
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')