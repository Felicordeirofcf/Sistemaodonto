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
import json

logger = logging.getLogger(__name__)

bp = Blueprint('marketing_campaigns', __name__)

# Configurações da API Evolution
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
    data = request.get_json() or {}

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
    full_tracking_url = f"{base_url}/api/marketing/c/{code}"

    return jsonify({
        "id": new_campaign.id,
        "name": new_campaign.name,
        "tracking_code": code,
        "tracking_url": full_tracking_url,
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
        "tracking_url": f"{base_url}/api/marketing/c/{c.tracking_code}",
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
    data = request.get_json() or {}

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
        for lead in leads:
            lead.campaign_id = None

        db.session.delete(camp)
        db.session.commit()
        return jsonify({"message": "Campanha excluída"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# 2. ROTA DE RASTREAMENTO (LÓGICA DE NÚMERO FIXO)
# ==============================================================================

@bp.route('/c/<code>', methods=['GET'])
def track_click_and_redirect(code):
    try:
        campaign = Campaign.query.filter_by(tracking_code=code).first()

        if not campaign:
            return redirect("https://www.google.com/search?q=Erro+Link+Nao+Encontrado")

        if not campaign.active:
            return redirect("https://www.google.com/search?q=Campanha+Pausada")

        # 1. Registra clique
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
            db.session.rollback()
            logger.warning(f"⚠️ Erro ao salvar métrica: {e}")

        # 2. LÓGICA DEFINITIVA: Pega o número direto do cadastro da clínica
        # Isso evita que o sistema precise consultar a API Evolution no momento do clique
        target_phone = campaign.clinic.whatsapp_number
        
        # Caso a clínica ainda não tenha o número cadastrado, usa o seu número padrão como segurança
        if not target_phone:
            target_phone = "5521987708652" 
        
        # Limpa o número para garantir que tenha apenas dígitos
        target_phone = "".join(filter(str.isdigit, target_phone))

        # 3. Redireciona para o WhatsApp
        text_encoded = urllib.parse.quote(campaign.whatsapp_message_template or "")
        whatsapp_url = f"https://api.whatsapp.com/send?phone={target_phone}&text={text_encoded}"

        logger.info(f"🚀 Redirecionando Lead para o WhatsApp da Clínica: {target_phone}")
        return redirect(whatsapp_url)

    except Exception as e:
        logger.error(f"🔥 ERRO CRÍTICO NO REDIRECT: {e}")
        return redirect(f"https://www.google.com/search?q=Erro+Sistema+Odonto+{urllib.parse.quote(str(e))}")


# ==============================================================================
# 3. QR CODE
# ==============================================================================

@bp.route('/campaigns/<int:campaign_id>/qr', methods=['GET'])
def get_qr_code(campaign_id):
    try:
        camp = Campaign.query.get_or_404(campaign_id)
        base_url = request.host_url.rstrip('/')
        link = f"{base_url}/api/marketing/c/{camp.tracking_code}"

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(link)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')

        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')

    except Exception as e:
        logger.error(f"Erro ao gerar QR: {e}")
        return jsonify({"error": "Erro ao gerar QR"}), 500