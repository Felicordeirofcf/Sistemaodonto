from flask import Blueprint, request, jsonify
from app.models import db, Clinic, CRMStage, CRMCard, Lead, Campaign, LeadEvent
import logging
import json
import re

logger = logging.getLogger(__name__)
bp = Blueprint('marketing_webhook', __name__)

# -------------------------
# Helpers
# -------------------------

def _get_json_body():
    data = request.get_json(silent=True)
    if data is not None:
        return data

    raw = (request.get_data(as_text=True) or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None

def _as_dict(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        v = value.strip()
        if v.startswith("{") and v.endswith("}"):
            try:
                return json.loads(v)
            except Exception:
                return {}
    return {}

def _normalize_phone_from_jid(jid: str) -> str:
    if not jid or not isinstance(jid, str):
        return ""
    base = jid.split("@")[0]
    base = base.split(":")[0]
    return base

def _extract_message_text(payload: dict) -> str:
    msg = payload.get("message") or {}
    if not isinstance(msg, dict):
        return ""

    if "conversation" in msg:
        return (msg.get("conversation") or "").strip()

    ext = msg.get("extendedTextMessage")
    if isinstance(ext, dict):
        return (ext.get("text") or "").strip()

    btn = msg.get("buttonsResponseMessage")
    if isinstance(btn, dict):
        return (btn.get("selectedDisplayText") or btn.get("selectedButtonId") or "").strip()

    lst = msg.get("listResponseMessage")
    if isinstance(lst, dict):
        single = lst.get("singleSelectReply") or {}
        if isinstance(single, dict):
            return (single.get("selectedRowId") or "").strip()
        return (lst.get("title") or "").strip()

    if "text" in msg:
        return (msg.get("text") or "").strip()

    return ""

def _extract_instance_owner(data: dict) -> str:
    if not isinstance(data, dict):
        return ""

    inst_raw = data.get("instance", {})
    inst = _as_dict(inst_raw)

    owner = (
        (inst.get("owner") if isinstance(inst, dict) else "")
        or data.get("instanceOwner")
        or data.get("owner")
        or ""
    )
    return owner.strip() if isinstance(owner, str) else ""

def _extract_tracking_code(message_text: str) -> str:
    """
    Aceita variações:
      [ref:CODE]
      ref:CODE
      ref=CODE
      ?ref=CODE
      utm_campaign=CODE
    """
    if not message_text:
        return ""

    patterns = [
        r"\[ref:(?P<code>[A-Za-z0-9_\-]{3,64})\]",
        r"\bref[:=](?P<code>[A-Za-z0-9_\-]{3,64})\b",
        r"[?&]ref=(?P<code>[A-Za-z0-9_\-]{3,64})",
        r"\butm_campaign=(?P<code>[A-Za-z0-9_\-]{3,64})\b",
    ]

    for p in patterns:
        m = re.search(p, message_text, flags=re.IGNORECASE)
        if m:
            return (m.group("code") or "").strip()

    return ""

def garantir_etapas_crm(clinic_id):
    etapas_padrao = [
        {"nome": "Novo Lead", "cor": "#3b82f6", "is_initial": True},
        {"nome": "Contactado", "cor": "#f59e0b", "is_initial": False},
        {"nome": "Agendado", "cor": "#10b981", "is_initial": False},
        {"nome": "Avaliado", "cor": "#8b5cf6", "is_initial": False},
        {"nome": "Perdido", "cor": "#ef4444", "is_initial": False}
    ]

    exists = CRMStage.query.filter_by(clinic_id=clinic_id).first()
    if exists:
        return

    logger.info(f"🛠️ Criando etapas padrão do CRM para clínica {clinic_id}")
    for i, etapa in enumerate(etapas_padrao):
        db.session.add(CRMStage(
            clinic_id=clinic_id,
            nome=etapa["nome"],
            cor=etapa["cor"],
            ordem=i,
            is_initial=etapa["is_initial"],
            is_success=(etapa["nome"] == "Agendado")
        ))
    db.session.commit()


# -------------------------
# Routes
# -------------------------

@bp.route('/webhook/whatsapp', methods=['POST'])
@bp.route('/webhook/whatsapp/messages-upsert', methods=['POST'])
def whatsapp_webhook():
    data = _get_json_body()

    if not data or not isinstance(data, dict):
        return jsonify({"status": "ignored", "reason": "no json"}), 200

    # Alguns provedores mandam direto o payload, outros dentro de "data"
    payload = data.get("data") if isinstance(data.get("data"), dict) else data
    if not isinstance(payload, dict):
        return jsonify({"status": "ignored", "reason": "invalid payload"}), 200

    key = payload.get('key') or {}
    if not isinstance(key, dict):
        return jsonify({"status": "ignored", "reason": "no key"}), 200

    if key.get('fromMe') is True:
        return jsonify({"status": "ignored", "reason": "from_me"}), 200

    remote_jid = key.get('remoteJid') or ""
    phone = _normalize_phone_from_jid(remote_jid)
    if not phone:
        return jsonify({"status": "ignored", "reason": "no phone"}), 200

    push_name = payload.get('pushName') or 'Paciente'
    message_text = _extract_message_text(payload)

    # IMPORTANTE: se não tem mensagem, não tem lead (evento não representa clique)
    if not (message_text or "").strip():
        return jsonify({"status": "ignored", "reason": "no text"}), 200

    # Identificação da clínica por owner (robusto)
    instance_owner = _extract_instance_owner(data)
    owner_phone = _normalize_phone_from_jid(instance_owner)

    clinic_id = 1
    if owner_phone:
        clinic = Clinic.query.filter_by(whatsapp_number=owner_phone).first()
        if clinic:
            clinic_id = clinic.id

    garantir_etapas_crm(clinic_id)

    # Detecta campanha por ref no texto
    code = _extract_tracking_code(message_text)
    campaign = None
    if code:
        # se seu banco for case-sensitive, isso ajuda:
        campaign = Campaign.query.filter(Campaign.tracking_code.ilike(code)).first()

    # Se já existe card aberto, só registra evento e sai
    existing_card = CRMCard.query.filter(
        CRMCard.clinic_id == clinic_id,
        CRMCard.paciente_phone == phone,
        CRMCard.status == 'open'
    ).first()

    try:
        if existing_card:
            db.session.add(LeadEvent(
                campaign_id=campaign.id if campaign else None,
                event_type='msg_in',
                metadata_json={
                    'phone': phone,
                    'push_name': push_name,
                    'message': message_text,
                    'clinic_id': clinic_id,
                    'owner_phone': owner_phone,
                    'note': 'already_in_crm'
                }
            ))
            db.session.commit()
            return jsonify({"status": "processed", "reason": "existing_card"}), 200

        # Cria Lead/Card mesmo sem campanha (não perde lead!)
        stage = CRMStage.query.filter_by(clinic_id=clinic_id, is_initial=True).first()
        if not stage:
            return jsonify({"status": "ignored", "reason": "no initial stage"}), 200

        source_text = f"Campanha: {campaign.name}" if campaign else "WhatsApp (orgânico)"

        novo_lead = Lead(
            clinic_id=clinic_id,
            campaign_id=campaign.id if campaign else None,
            name=push_name,
            phone=phone,
            source=source_text,
            status='novo'
        )
        db.session.add(novo_lead)

        novo_card = CRMCard(
            clinic_id=clinic_id,
            stage_id=stage.id,
            paciente_nome=push_name,
            paciente_phone=phone,
            historico_conversas=f"{source_text}: {message_text}",
            valor_proposta=0,
            status='open'
        )
        db.session.add(novo_card)

        if campaign:
            campaign.leads_count = (campaign.leads_count or 0) + 1

        db.session.add(LeadEvent(
            campaign_id=campaign.id if campaign else None,
            event_type='msg_in',
            metadata_json={
                'phone': phone,
                'push_name': push_name,
                'message': message_text,
                'clinic_id': clinic_id,
                'owner_phone': owner_phone,
                'tracking_code': code or None
            }
        ))

        db.session.commit()
        return jsonify({
            "status": "processed",
            "campaign": campaign.id if campaign else None,
            "tracking_code": code or None
        }), 200

    except Exception as e:
        logger.exception(f"❌ Erro no webhook WhatsApp: {e}")
        db.session.rollback()
        return jsonify({"status": "error"}), 500
