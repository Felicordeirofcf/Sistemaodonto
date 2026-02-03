from flask import Blueprint, request, jsonify
from app.models import db, Clinic, CRMStage, CRMCard, Lead, Campaign, LeadEvent, MessageLog
import logging
import json
import re
import os
import requests
from datetime import datetime

logger = logging.getLogger(__name__)
bp = Blueprint('marketing_webhook', __name__)

# --- CONFIGURAÇÕES ---
EVOLUTION_API_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")

# -------------------------
# Helpers
# -------------------------

def _get_json_body():
    data = request.get_json(silent=True)
    if data is not None:
        return data
    raw = (request.get_data(as_text=True) or "").strip()
    if not raw: return None
    try: return json.loads(raw)
    except: return None

def _as_dict(value):
    if isinstance(value, dict): return value
    if isinstance(value, str):
        v = value.strip()
        if v.startswith("{") and v.endswith("}"):
            try: return json.loads(v)
            except: return {}
    return {}

def _only_digits(value: str) -> str:
    return "".join(filter(str.isdigit, value or ""))

def _normalize_phone_from_jid(jid: str) -> str:
    if not jid or not isinstance(jid, str): return ""
    return _only_digits(jid.split("@")[0].split(":")[0])

def _extract_message_text(payload: dict) -> str:
    msg = payload.get("message") or {}
    if not isinstance(msg, dict): return ""
    if "conversation" in msg: return (msg.get("conversation") or "").strip()
    ext = msg.get("extendedTextMessage")
    if isinstance(ext, dict): return (ext.get("text") or "").strip()
    btn = msg.get("buttonsResponseMessage")
    if isinstance(btn, dict): return (btn.get("selectedDisplayText") or btn.get("selectedButtonId") or "").strip()
    lst = msg.get("listResponseMessage")
    if isinstance(lst, dict):
        single = lst.get("singleSelectReply") or {}
        if isinstance(single, dict): return (single.get("selectedRowId") or "").strip()
        return (lst.get("title") or "").strip()
    if "text" in msg: return (msg.get("text") or "").strip()
    return ""

def _extract_instance_owner(container: dict) -> str:
    if not isinstance(container, dict): return ""
    inst = _as_dict(container.get("instance", {}))
    owner = inst.get("owner") or container.get("instanceOwner") or container.get("owner") or ""
    return owner.strip() if isinstance(owner, str) else ""

def _extract_instance_name(container: dict) -> str:
    if not isinstance(container, dict): return ""
    inst = container.get("instance")
    if isinstance(inst, str) and inst.strip(): return inst.strip()
    if isinstance(inst, dict):
        for k in ("instanceName", "name"):
            if isinstance(inst.get(k), str) and inst.get(k).strip(): return inst.get(k).strip()
    return container.get("instanceName", "").strip()

def _extract_tracking_code(message_text: str) -> str:
    if not message_text: return ""
    patterns = [r"\[ref:(?P<code>[A-Za-z0-9_\-]{3,64})\]", r"\bref[:=](?P<code>[A-Za-z0-9_\-]{3,64})\b"]
    for p in patterns:
        m = re.search(p, message_text, flags=re.IGNORECASE)
        if m: return (m.group("code") or "").strip()
    return ""

def _is_group_message(payload: dict, key: dict, remote_jid: str) -> bool:
    if isinstance(remote_jid, str) and remote_jid.endswith("@g.us"): return True
    if payload.get("isGroup") is True or key.get("participant") or payload.get("participant"): return True
    return False

def garantir_etapas_crm(clinic_id):
    exists = CRMStage.query.filter_by(clinic_id=clinic_id).first()
    if exists: return
    etapas = [
        {"nome": "Novo Lead", "cor": "yellow", "is_initial": True},
        {"nome": "Contactado", "cor": "blue", "is_initial": False},
        {"nome": "Agendado", "cor": "green", "is_initial": False, "is_success": True},
        {"nome": "Perdido", "cor": "red", "is_initial": False}
    ]
    for i, etapa in enumerate(etapas):
        db.session.add(CRMStage(clinic_id=clinic_id, nome=etapa["nome"], cor=etapa["cor"], ordem=i, is_initial=etapa["is_initial"], is_success=etapa.get("is_success", False)))
    db.session.commit()

def _send_whatsapp_reply(clinic_id, to_phone, text):
    instance_name = f"clinica_v3_{clinic_id}"
    url = f"{EVOLUTION_API_URL}/message/sendText/{instance_name}"
    headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}
    payload = {"number": to_phone, "text": text, "delay": 1200}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        log = MessageLog(clinic_id=clinic_id, direction="out", body=text, status="sent" if r.status_code in (200, 201) else "failed")
        db.session.add(log)
        db.session.commit()
        return r.status_code in (200, 201)
    except Exception as e:
        logger.error(f"Erro ao enviar resposta automática: {e}")
        return False

# -------------------------
# Routes
# -------------------------

@bp.route('/webhook/whatsapp', methods=['POST'])
@bp.route('/webhook/whatsapp/messages-upsert', methods=['POST'])
def whatsapp_webhook():
    data = _get_json_body()
    if not data or not isinstance(data, dict): return jsonify({"status": "ignored"}), 200
    payload = data.get("data") if isinstance(data.get("data"), dict) else data
    key = payload.get('key') or {}
    if key.get('fromMe') is True: return jsonify({"status": "ignored"}), 200
    remote_jid = key.get('remoteJid') or ""
    if _is_group_message(payload, key, remote_jid): return jsonify({"status": "ignored"}), 200
    phone = _normalize_phone_from_jid(remote_jid)
    if not phone: return jsonify({"status": "ignored"}), 200
    
    push_name = (payload.get('pushName') or 'Paciente').strip()
    message_text = _extract_message_text(payload)
    if not message_text: return jsonify({"status": "ignored"}), 200

    # Identificação da Clínica
    owner_raw = _extract_instance_owner(data) or _extract_instance_owner(payload)
    owner_phone = _normalize_phone_from_jid(owner_raw)
    instance_name = _extract_instance_name(data) or _extract_instance_name(payload)

    clinic = None
    if owner_phone: clinic = Clinic.query.filter_by(whatsapp_number=owner_phone).first()
    if not clinic and instance_name and instance_name.startswith("clinica_v3_"):
        try: clinic = Clinic.query.get(int(instance_name.replace("clinica_v3_", "")))
        except: pass
    if not clinic: clinic = Clinic.query.filter(Clinic.id == 1).first()
    if not clinic: return jsonify({"status": "ignored"}), 200

    clinic_id = clinic.id
    garantir_etapas_crm(clinic_id)

    # Tracking de Campanha
    code = _extract_tracking_code(message_text)
    campaign = Campaign.query.filter(Campaign.tracking_code.ilike(code)).first() if code else None
    source_text = f"Campanha: {campaign.name}" if campaign else "WhatsApp (orgânico)"

    try:
        # Log Event
        db.session.add(LeadEvent(campaign_id=campaign.id if campaign else None, event_type='msg_in', metadata_json={"phone": phone, "push_name": push_name, "message": message_text, "clinic_id": clinic_id}))

        # Busca Card Aberto
        existing_card = CRMCard.query.filter(CRMCard.clinic_id == clinic_id, CRMCard.paciente_phone == phone, CRMCard.status == 'open').first()

        if existing_card:
            prev = existing_card.historico_conversas or ""
            existing_card.historico_conversas = (prev + f"\n{push_name}: {message_text}").strip()
            existing_card.ultima_interacao = datetime.utcnow()
            db.session.commit()
            return jsonify({"status": "processed"}), 200

        # Novo Lead / Card
        lead = Lead.query.filter_by(clinic_id=clinic_id, phone=phone).first()
        if not lead:
            lead = Lead(clinic_id=clinic_id, campaign_id=campaign.id if campaign else None, name=push_name, phone=phone, source=source_text, status='novo')
            db.session.add(lead)
        
        stage = CRMStage.query.filter_by(clinic_id=clinic_id, is_initial=True).first()
        if stage:
            novo_card = CRMCard(clinic_id=clinic_id, stage_id=stage.id, paciente_nome=push_name, paciente_phone=phone, historico_conversas=f"{source_text}: {message_text}", status='open', ultima_interacao=datetime.utcnow())
            db.session.add(novo_card)

        if campaign:
            campaign.leads_count = (campaign.leads_count or 0) + 1
            # --- CHATBOT: Resposta Automática da Campanha ---
            # Se a campanha tiver uma mensagem configurada ou se quisermos uma saudação padrão
            reply_text = f"Olá {push_name}! Recebemos seu interesse na campanha *{campaign.name}*. Em breve um de nossos especialistas entrará em contato para agendar sua avaliação! 🦷✨"
            _send_whatsapp_reply(clinic_id, phone, reply_text)

        db.session.commit()
        return jsonify({"status": "processed", "clinic_id": clinic_id}), 200

    except Exception as e:
        logger.exception(f"Erro no webhook: {e}")
        db.session.rollback()
        return jsonify({"status": "error"}), 500
