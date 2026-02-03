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
# Helpers
# ==============================================================================

def safe_json_to_dict(value):
    """Aceita dict, string JSON ou None e devolve dict ou None."""
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return None
    return None

def jid_to_phone(jid: str) -> str | None:
    """
    Converte JID (ex: 5511999999999@s.whatsapp.net ou 5511...:1@s.whatsapp.net)
    para apenas número (5511999999999).
    """
    if not jid or not isinstance(jid, str):
        return None
    base = jid.split("@")[0]
    base = base.split(":")[0]
    base = base.strip()
    return base or None

def normalize_phone(phone: str) -> str | None:
    """Normaliza telefone para formato aceito pelo WhatsApp (apenas dígitos)."""
    if not phone or not isinstance(phone, str):
        return None
    phone = phone.strip()
    phone = phone.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    phone = "".join(ch for ch in phone if ch.isdigit())
    return phone or None

def get_connected_phone_for_clinic(clinic_id: int) -> str | None:
    """
    Busca o telefone do WhatsApp conectado via QR Code.
    Prioridade:
      1) Cache no banco (WhatsAppConnection.session_data['me']['id'])
      2) Evolution API (/instance/fetchInstances) -> instance.owner
         e atualiza o cache no banco.
    """
    conn = WhatsAppConnection.query.filter_by(clinic_id=clinic_id).first()

    # 1) Tenta pelo banco (session_data)
    if conn and conn.session_data:
        sd = safe_json_to_dict(conn.session_data)
        if sd and isinstance(sd, dict):
            me = sd.get("me")
            if isinstance(me, dict):
                jid = me.get("id") or me.get("jid")
                phone = normalize_phone(jid_to_phone(jid))
                if phone:
                    return phone

            # Alguns providers salvam direto como owner/jid
            owner = sd.get("owner") or sd.get("jid") or sd.get("id")
            phone = normalize_phone(jid_to_phone(owner))
            if phone:
                return phone

    # 2) Tenta na Evolution API e atualiza cache
    # OBS: no Render, localhost NÃO funciona; garanta WHATSAPP_QR_SERVICE_URL correto.
    if not EVOLUTION_API_URL or not EVOLUTION_API_KEY:
        logger.warning("EVOLUTION_API_URL ou EVOLUTION_API_KEY não configurado.")
        return None

    try:
        url = f"{EVOLUTION_API_URL}/instance/fetchInstances"
        headers = {"apikey": EVOLUTION_API_KEY}
        resp = requests.get(url, headers=headers, timeout=6)

        if resp.status_code != 200:
            logger.error(f"Evolution API erro status={resp.status_code} body={resp.text[:200]}")
            return None

        instances = resp.json() if resp.content else []
        if not isinstance(instances, list):
            logger.error("Evolution API retornou formato inesperado (não é lista).")
            return None

        # Procura instância conectada (ajuste status conforme sua Evolution)
        active_instance = None
        for i in instances:
            inst = (i or {}).get("instance", {}) if isinstance(i, dict) else {}
            status = str(inst.get("status", "")).lower()
            if status in ["open", "connected", "connecting", "online"]:
                active_instance = i
                break

        if not active_instance:
            return None

        inst = active_instance.get("instance", {})
        owner_jid = inst.get("owner") or inst.get("me") or inst.get("jid")
        phone = normalize_phone(jid_to_phone(owner_jid))
        if not phone:
            return None

        # Atualiza cache no banco
        try:
            if not conn:
                conn = WhatsAppConnection(clinic_id=clinic_id)

            conn.session_data = {"me": {"id": owner_jid}}
            conn.status = "connected"
            db.session.add(conn)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.warning(f"Falha ao atualizar cache WhatsAppConnection: {e}")

        return phone

    except Exception as e:
        logger.error(f"Erro consultando Evolution API: {e}")
        return None


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
# 2. ROTA DE RASTREAMENTO (ABRE WHATSAPP)
# ==============================================================================

@bp.route('/c/<code>', methods=['GET'])
def track_click_and_redirect(code):
    try:
        campaign = Campaign.query.filter_by(tracking_code=code).first()

        if not campaign:
            return redirect("https://www.google.com/search?q=Erro+Link+Nao+Encontrado+SistemaOdonto")

        if not campaign.active:
            return redirect("https://www.google.com/search?q=Campanha+Pausada+Pelo+Anunciante")

        # Registra clique sem travar
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
            logger.warning(f"⚠️ Erro ao salvar métrica (ignorado): {e}")

        # ✅ Busca o telefone conectado via QR Code (cache banco -> Evolution)
        target_phone = get_connected_phone_for_clinic(campaign.clinic_id)

        if not target_phone:
            logger.error("❌ Nenhum telefone conectado encontrado (WhatsAppConnection/Evolution).")
            return redirect("https://www.google.com/search?q=Erro+WhatsApp+Nao+Conectado+Verifique+Painel")

        # Redireciona para WhatsApp
        text_encoded = urllib.parse.quote(campaign.whatsapp_message_template or "")
        whatsapp_url = f"https://api.whatsapp.com/send?phone={target_phone}&text={text_encoded}"

        return redirect(whatsapp_url)

    except Exception as e:
        logger.error(f"🔥 ERRO CRÍTICO NO REDIRECT: {e}")
        return redirect(f"https://www.google.com/search?q=Erro+Sistema+Interno+{urllib.parse.quote(str(e))}")


# ==============================================================================
# 3. QR CODE (DO LINK DA CAMPANHA)
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
