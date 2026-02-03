from flask import Blueprint, request, jsonify, redirect, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Campaign, Lead, LeadEvent, Clinic
import shortuuid
import qrcode
from io import BytesIO
import logging
import urllib.parse
import os

logger = logging.getLogger(__name__)
bp = Blueprint('marketing_campaigns', __name__)

DEFAULT_CLINIC_WHATSAPP = os.getenv("DEFAULT_CLINIC_WHATSAPP", "")

# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def _get_clinic_id_from_jwt() -> int:
    identity = get_jwt_identity()
    if isinstance(identity, dict) and identity.get("clinic_id"):
        try:
            return int(identity["clinic_id"])
        except Exception:
            return 1
    return 1

def _safe_int(value, default=0) -> int:
    try:
        return int(value)
    except Exception:
        return default

def _only_digits(value: str) -> str:
    return "".join(filter(str.isdigit, value or ""))

def _generate_unique_code(length=5, max_tries=30) -> str:
    """
    Gera tracking_code curto e evita colisão.
    """
    su = shortuuid.ShortUUID()
    for _ in range(max_tries):
        code = su.random(length=length)
        exists = Campaign.query.filter_by(tracking_code=code).first()
        if not exists:
            return code
    return su.random(length=8)

def _ensure_ref_in_message(msg_template: str, code: str) -> str:
    msg_template = (msg_template or "Olá, gostaria de saber mais.").strip()

    # Ajuda na conversão (sem mensagem enviada, você não recebe webhook)
    if "enviar" not in msg_template.lower():
        msg_template = "Olá! Clique em enviar para iniciar o atendimento. " + msg_template

    ref_tag = f"[ref:{code}]"
    if ref_tag not in msg_template:
        msg_template = msg_template + f" {ref_tag}"

    return msg_template


# ==============================================================================
# 1. GESTÃO DE CAMPANHAS
# ==============================================================================

@bp.route('/campaigns', methods=['POST'])
@jwt_required()
def create_campaign():
    clinic_id = _get_clinic_id_from_jwt()
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Campo 'name' é obrigatório"}), 400

    slug = (data.get("slug") or "").strip() or None

    landing_data = data.get("landing_data", {}) or {}
    if not isinstance(landing_data, dict):
        return jsonify({"error": "Campo 'landing_data' deve ser um objeto JSON"}), 400

    code = _generate_unique_code(length=5)
    msg_template = _ensure_ref_in_message(data.get("message"), code)

    new_campaign = Campaign(
        clinic_id=clinic_id,
        name=name,
        slug=slug,
        tracking_code=code,
        whatsapp_message_template=msg_template,
        landing_page_data=landing_data,
        active=True,
    )

    # Se o model não tiver default 0, setamos aqui com segurança.
    if hasattr(new_campaign, "clicks_count") and getattr(new_campaign, "clicks_count", None) is None:
        new_campaign.clicks_count = 0
    if hasattr(new_campaign, "leads_count") and getattr(new_campaign, "leads_count", None) is None:
        new_campaign.leads_count = 0

    db.session.add(new_campaign)
    db.session.commit()

    base_url = request.host_url.rstrip('/')
    tracking_url = f"{base_url}/api/marketing/c/{code}"

    return jsonify({
        "id": new_campaign.id,
        "name": new_campaign.name,
        "tracking_code": code,
        "tracking_url": tracking_url,
        "active": bool(new_campaign.active),
        "clicks": _safe_int(getattr(new_campaign, "clicks_count", 0), 0),
        "leads": _safe_int(getattr(new_campaign, "leads_count", 0), 0),
        "qr_code_url": f"{base_url}/api/marketing/campaigns/{new_campaign.id}/qr"
    }), 201


@bp.route('/campaigns', methods=['GET'])
@jwt_required()
def list_campaigns():
    clinic_id = _get_clinic_id_from_jwt()
    base_url = request.host_url.rstrip('/')

    campaigns = Campaign.query.filter_by(clinic_id=clinic_id).order_by(Campaign.created_at.desc()).all()

    return jsonify([{
        "id": c.id,
        "name": c.name,
        "tracking_code": c.tracking_code,
        "tracking_url": f"{base_url}/api/marketing/c/{c.tracking_code}",
        "active": bool(c.active),
        "clicks": _safe_int(getattr(c, "clicks_count", 0), 0),
        "leads": _safe_int(getattr(c, "leads_count", 0), 0),
        "qr_code_url": f"{base_url}/api/marketing/campaigns/{c.id}/qr"
    } for c in campaigns]), 200


@bp.route('/campaigns/<int:id>/status', methods=['PATCH'])
@jwt_required()
def toggle_status(id):
    clinic_id = _get_clinic_id_from_jwt()
    camp = Campaign.query.filter_by(id=id, clinic_id=clinic_id).first_or_404()

    data = request.get_json(silent=True) or {}
    if 'active' in data:
        camp.active = bool(data['active'])
        db.session.commit()

    return jsonify({"message": "Status atualizado", "active": bool(camp.active)}), 200


@bp.route('/campaigns/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_campaign(id):
    clinic_id = _get_clinic_id_from_jwt()
    camp = Campaign.query.filter_by(id=id, clinic_id=clinic_id).first_or_404()

    try:
        LeadEvent.query.filter_by(campaign_id=camp.id).delete(synchronize_session=False)
        Lead.query.filter_by(campaign_id=camp.id).update(
            {Lead.campaign_id: None},
            synchronize_session=False
        )

        db.session.delete(camp)
        db.session.commit()
        return jsonify({"message": "Campanha excluída"}), 200

    except Exception as e:
        db.session.rollback()
        logger.exception(f"Erro ao excluir campanha {id}: {e}")
        return jsonify({"error": "Falha ao excluir campanha"}), 500


# ==============================================================================
# 2. ROTA DE RASTREAMENTO (redirect)
# ==============================================================================

@bp.route('/c/<code>', methods=['GET'])
def track_click_and_redirect(code):
    try:
        campaign = Campaign.query.filter_by(tracking_code=code).first()
        if not campaign:
            return redirect("https://www.google.com/search?q=Erro+Link+Nao+Encontrado")

        if not campaign.active:
            return redirect("https://www.google.com/search?q=Campanha+Pausada")

        # 1) registra clique sem quebrar em None
        try:
            current = _safe_int(getattr(campaign, "clicks_count", 0), 0)
            if hasattr(campaign, "clicks_count"):
                campaign.clicks_count = current + 1

            db.session.add(LeadEvent(
                campaign_id=campaign.id,
                event_type='click',
                metadata_json={
                    "user_agent": request.headers.get("User-Agent", ""),
                    "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
                }
            ))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.warning(f"⚠️ Erro ao salvar métrica de clique: {e}")

        # 2) número âncora: whatsapp da clínica
        clinic = Clinic.query.get(campaign.clinic_id)
        target_phone = _only_digits(getattr(clinic, "whatsapp_number", "") if clinic else "")

        if not target_phone:
            target_phone = _only_digits(DEFAULT_CLINIC_WHATSAPP)

        if not target_phone:
            return redirect("https://www.google.com/search?q=Erro+WhatsApp+Nao+Configurado")

        # 3) garante que a mensagem contenha o ref
        msg_template = _ensure_ref_in_message(campaign.whatsapp_message_template or "", campaign.tracking_code)

        # 4) redirect pro whatsapp
        text_encoded = urllib.parse.quote(msg_template, safe="")
        whatsapp_url = f"https://api.whatsapp.com/send?phone={target_phone}&text={text_encoded}"

        logger.info(f"🚀 Redirect campanha={campaign.id} clinic={campaign.clinic_id} -> wa={target_phone}")
        return redirect(whatsapp_url)

    except Exception as e:
        logger.exception(f"🔥 ERRO CRÍTICO NO REDIRECT: {e}")
        return redirect("https://www.google.com/search?q=Erro+Sistema+Odonto")


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

        # Opcional: cache leve no client/CDN
        return send_file(img_io, mimetype='image/png', max_age=60)

    except Exception as e:
        logger.exception(f"Erro ao gerar QR: {e}")
        return jsonify({"error": "Erro ao gerar QR"}), 500
