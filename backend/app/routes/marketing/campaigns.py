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

# Configs (mantive, mas aqui você não está usando requests/WhatsAppConnection)
EVOLUTION_API_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------

def _get_clinic_id_from_jwt():
    identity = get_jwt_identity()
    if isinstance(identity, dict) and identity.get("clinic_id"):
        return identity["clinic_id"]
    return 1

def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default

def _generate_unique_code(length=5, max_tries=20):
    """
    Gera tracking_code curto e evita colisão.
    """
    su = shortuuid.ShortUUID()
    for _ in range(max_tries):
        code = su.random(length=length)
        exists = Campaign.query.filter_by(tracking_code=code).first()
        if not exists:
            return code
    # fallback (se der azar absurdo)
    return su.random(length=8)

def _ensure_ref_in_message(msg_template: str, code: str) -> str:
    msg_template = (msg_template or "Olá, gostaria de saber mais.").strip()

    # (Opcional) instrução para aumentar conversão (usuário precisa enviar msg)
    # Você pode remover se não quiser.
    if "enviar" not in msg_template.lower():
        msg_template = "Olá! Clique em enviar para iniciar o atendimento. " + msg_template

    # garante ref
    ref_tag = f"[ref:{code}]"
    if ref_tag not in msg_template:
        # coloca separado para facilitar parsing
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

    code = _generate_unique_code(length=5)

    msg_template = _ensure_ref_in_message(data.get('message'), code)

    new_campaign = Campaign(
        clinic_id=clinic_id,
        name=name,
        slug=data.get('slug'),
        tracking_code=code,
        whatsapp_message_template=msg_template,
        landing_page_data=data.get('landing_data', {}) or {},
        active=True,
        clicks_count=0 if getattr(Campaign, "clicks_count", None) else None,  # não quebra se model não tiver default
        leads_count=0 if getattr(Campaign, "leads_count", None) else None
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
        # Remove eventos
        LeadEvent.query.filter_by(campaign_id=camp.id).delete(synchronize_session=False)

        # Desvincula leads
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

        # 1) Registra clique (sem quebrar em None)
        try:
            current = _safe_int(getattr(campaign, "clicks_count", 0), 0)
            campaign.clicks_count = current + 1

            db.session.add(LeadEvent(
                campaign_id=campaign.id,
                event_type='click',
                metadata_json={
                    'user_agent': request.headers.get('User-Agent', ''),
                    'ip': request.headers.get('X-Forwarded-For', request.remote_addr),
                }
            ))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.warning(f"⚠️ Erro ao salvar métrica de clique: {e}")

        # 2) Número âncora: WhatsApp da clínica
        clinic = Clinic.query.get(campaign.clinic_id)
        target_phone = clinic.whatsapp_number if clinic else None

        if not target_phone:
            # Evite hardcode em produção; melhor ter um env var DEFAULT_CLINIC_WHATSAPP
            target_phone = os.getenv("DEFAULT_CLINIC_WHATSAPP", "5521987708652")

        target_phone = "".join(filter(str.isdigit, target_phone))

        # 3) Garante que a mensagem contenha o ref (por segurança)
        msg_template = _ensure_ref_in_message(campaign.whatsapp_message_template or "", campaign.tracking_code)

        # 4) Redireciona para WhatsApp
        # api.whatsapp.com funciona bem em desktop/mobile.
        text_encoded = urllib.parse.quote(msg_template, safe="")
        whatsapp_url = f"https://api.whatsapp.com/send?phone={target_phone}&text={text_encoded}"

        logger.info(f"🚀 Redirect campanha={campaign.id} clinic={campaign.clinic_id} -> wa phone={target_phone}")
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
        return send_file(img_io, mimetype='image/png')

    except Exception as e:
        logger.exception(f"Erro ao gerar QR: {e}")
        return jsonify({"error": "Erro ao gerar QR"}), 500
