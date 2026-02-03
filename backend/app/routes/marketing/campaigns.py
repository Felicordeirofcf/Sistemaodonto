from flask import Blueprint, request, jsonify, redirect, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Campaign, Lead, LeadEvent, WhatsAppConnection
import shortuuid
import qrcode
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('marketing_campaigns', __name__)

# ==============================================================================
# 1. GESTÃO DE CAMPANHAS (CRIAR, LISTAR, EDITAR, EXCLUIR)
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
        "active": c.active,  # Retorna se está pausada ou não
        "clicks": c.clicks_count,
        "leads": c.leads_count
    } for c in campaigns]), 200

# ✅ NOVA ROTA: ALTERAR STATUS (PAUSAR / RETOMAR)
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

# ✅ NOVA ROTA: EXCLUIR CAMPANHA
@bp.route('/campaigns/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_campaign(id):
    identity = get_jwt_identity()
    clinic_id = identity.get('clinic_id') if isinstance(identity, dict) else 1
    
    camp = Campaign.query.filter_by(id=id, clinic_id=clinic_id).first_or_404()
    
    try:
        # Primeiro, removemos os eventos e desvinculamos leads para não dar erro de chave estrangeira
        LeadEvent.query.filter_by(campaign_id=id).delete()
        
        # Opção A: Excluir os leads também? (Geralmente não, apenas desvincula)
        # Leads vinculados ficam com campaign_id NULL
        leads = Lead.query.filter_by(campaign_id=id).all()
        for lead in leads:
            lead.campaign_id = None
        
        # Agora exclui a campanha
        db.session.delete(camp)
        db.session.commit()
        return jsonify({"message": "Campanha excluída com sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao excluir: {str(e)}"}), 500

# ==============================================================================
# 2. ROTA DE RASTREAMENTO
# ==============================================================================
@bp.route('/c/<code>', methods=['GET'])
def track_click_and_redirect(code):
    campaign = Campaign.query.filter_by(tracking_code=code).first()
    
    # Se não existe
    if not campaign:
        return f"<h1 style='text-align:center; margin-top:50px;'>⚠️ Link Inválido</h1>", 404

    # ✅ Se estiver PAUSADA
    if not campaign.active:
        return f"""
        <div style="font-family:sans-serif; text-align:center; padding:50px;">
            <h1>⏸️ Campanha Pausada</h1>
            <p>Esta oferta não está mais disponível no momento.</p>
        </div>
        """, 200
    
    # 1. Registra Métrica
    try:
        campaign.clicks_count += 1
        event = LeadEvent(
            campaign_id=campaign.id, 
            event_type='click',
            metadata_json={'user_agent': request.headers.get('User-Agent')}
        )
        db.session.add(event)
        db.session.commit()
    except: pass

    # 2. Redireciona
    target_phone = "5511999999999" # Fallback
    try:
        conn = WhatsAppConnection.query.filter_by(clinic_id=campaign.clinic_id, status='connected').first()
        if conn and conn.session_data:
            target_phone = conn.session_data.get('me', {}).get('id', '').split('@')[0] or target_phone
    except: pass

    import urllib.parse
    text_encoded = urllib.parse.quote(campaign.whatsapp_message_template)
    return redirect(f"https://wa.me/{target_phone}?text={text_encoded}")

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