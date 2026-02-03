from flask import Blueprint, request, jsonify
from app.models import db, Clinic, CRMStage, CRMCard, Lead, Campaign, LeadEvent
import logging
import json
import re
from datetime import datetime

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

def _only_digits(value: str) -> str:
    return "".join(filter(str.isdigit, value or ""))

def _normalize_phone_from_jid(jid: str) -> str:
    """
    '5511999999999@s.whatsapp.net' -> '5511999999999'
    também remove ':xyz'
    """
    if not jid or not isinstance(jid, str):
        return ""
    base = jid.split("@")[0]
    base = base.split(":")[0]
    return _only_digits(base)

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

def _extract_instance_owner(container: dict) -> str:
    """
    Aceita:
      - container["instance"] dict {"owner": "..."}
      - container["instance"] str
      - container["instanceOwner"] / container["owner"]
    """
    if not isinstance(container, dict):
        return ""

    inst_raw = container.get("instance", {})
    inst = _as_dict(inst_raw)

    owner = (
        (inst.get("owner") if isinstance(inst, dict) else "")
        or container.get("instanceOwner")
        or container.get("owner")
        or ""
    )
    return owner.strip() if isinstance(owner, str) else ""

def _extract_instance_name(container: dict) -> str:
    if not isinstance(container, dict):
        return ""
    inst = container.get("instance")
    if isinstance(inst, str) and inst.strip():
        return inst.strip()
    if isinstance(inst, dict):
        for k in ("instanceName", "name"):
            if isinstance(inst.get(k), str) and inst.get(k).strip():
                return inst.get(k).strip()
    if isinstance(container.get("instanceName"), str):
        return container.get("instanceName").strip()
    return ""

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

def _is_group_message(payload: dict, key: dict, remote_jid: str) -> bool:
    """
    Ignora grupos de forma robusta:
    - remoteJid termina com @g.us
    - payload.isGroup == True
    - key.participant existe (em grupo costuma existir)
    - alguns stubs/eventos sem texto em grupo
    """
    if isinstance(remote_jid, str) and remote_jid.endswith("@g.us"):
        return True

    if payload.get("isGroup") is True:
        return True

    participant = key.get("participant") or payload.get("participant")
    if participant:
        # Em geral, participant aparece em grupos
        return True

    # Alguns provedores mandam stub/eventos de grupo
    if payload.get("messageStubType") in (20, 21, 22, 23, 24, 25, 26, 27):
        return True

    return False

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

def _append_history(card: CRMCard, text: str):
    if not hasattr(card, "historico_conversas"):
        return
    prev = getattr(card, "historico_conversas", "") or ""
    setattr(card, "historico_conversas", (prev + "\n" + text).strip() if prev else text)

def _touch_last_interaction(card: CRMCard):
    if hasattr(card, "ultima_interacao"):
        setattr(card, "ultima_interacao", datetime.utcnow())

# -------------------------
# Routes
# -------------------------

@bp.route('/webhook/whatsapp', methods=['POST'])
@bp.route('/webhook/whatsapp/messages-upsert', methods=['POST'])
def whatsapp_webhook():
    data = _get_json_body()
    if not data or not isinstance(data, dict):
        return jsonify({"status": "ignored", "reason": "no json"}), 200

    # Alguns provedores mandam dentro de "data"
    payload = data.get("data") if isinstance(data.get("data"), dict) else data
    if not isinstance(payload, dict):
        return jsonify({"status": "ignored", "reason": "invalid payload"}), 200

    key = payload.get('key') or {}
    if not isinstance(key, dict):
        return jsonify({"status": "ignored", "reason": "no key"}), 200

    # ignora mensagens enviadas por você
    if key.get('fromMe') is True:
        return jsonify({"status": "ignored", "reason": "from_me"}), 200

    remote_jid = key.get('remoteJid') or ""
    if _is_group_message(payload, key, remote_jid):
        return jsonify({"status": "ignored", "reason": "group_message"}), 200

    # normaliza telefone (somente dígitos)
    phone = _normalize_phone_from_jid(remote_jid)
    if not phone:
        return jsonify({"status": "ignored", "reason": "no phone"}), 200

    push_name = (payload.get('pushName') or 'Paciente').strip()

    message_text = (_extract_message_text(payload) or "").strip()
    if not message_text:
        return jsonify({"status": "ignored", "reason": "no text"}), 200

    # --- Identificação da clínica ---
    owner_raw = _extract_instance_owner(data) or _extract_instance_owner(payload)
    owner_phone = _normalize_phone_from_jid(owner_raw)

    instance_name = _extract_instance_name(data) or _extract_instance_name(payload)

    clinic_id = 1
    clinic = None

    # 1) pelo número owner salvo na clínica
    if owner_phone:
        clinic = Clinic.query.filter_by(whatsapp_number=owner_phone).first()

    # 2) fallback: pelo nome da instância (se existir esse campo)
    if not clinic and instance_name and hasattr(Clinic, "whatsapp_instance"):
        clinic = Clinic.query.filter_by(whatsapp_instance=instance_name).first()

    if clinic:
        clinic_id = clinic.id

    garantir_etapas_crm(clinic_id)

    # --- Campanha ---
    code = _extract_tracking_code(message_text)
    campaign = None
    if code:
        campaign = Campaign.query.filter(Campaign.tracking_code.ilike(code)).first()

    source_text = f"Campanha: {campaign.name}" if campaign else "WhatsApp (orgânico)"

    # --- Procura card aberto ---
    existing_card = CRMCard.query.filter(
        CRMCard.clinic_id == clinic_id,
        CRMCard.paciente_phone == phone,
        CRMCard.status == 'open'
    ).first()

    try:
        # Sempre registra evento msg_in
        db.session.add(LeadEvent(
            campaign_id=campaign.id if campaign else None,
            event_type='msg_in',
            metadata_json={
                "phone": phone,
                "push_name": push_name,
                "message": message_text,
                "clinic_id": clinic_id,
                "owner_phone": owner_phone,
                "instance_name": instance_name,
                "tracking_code": code or None,
                "source": source_text,
                "note": "existing_card" if existing_card else "new_contact"
            }
        ))

        if existing_card:
            # Atualiza histórico e última interação
            _append_history(existing_card, f"{push_name}: {message_text}")
            _touch_last_interaction(existing_card)

            # Se a pessoa mandar o [ref] depois, atualiza o source no card/histórico
            # (opcional, mas ajuda)
            if campaign and hasattr(existing_card, "historico_conversas"):
                # só adiciona se ainda não tiver a campanha registrada no histórico
                if (existing_card.historico_conversas or "").lower().find("campanha:") == -1:
                    _append_history(existing_card, f"Origem: {source_text}")

            db.session.commit()
            return jsonify({"status": "processed", "reason": "existing_card"}), 200

        # --- Evita duplicar Lead ---
        existing_lead = Lead.query.filter_by(clinic_id=clinic_id, phone=phone).first()

        # Estágio inicial
        stage = CRMStage.query.filter_by(clinic_id=clinic_id, is_initial=True).first()
        if not stage:
            db.session.commit()
            return jsonify({"status": "ignored", "reason": "no initial stage"}), 200

        if not existing_lead:
            novo_lead = Lead(
                clinic_id=clinic_id,
                campaign_id=campaign.id if campaign else None,
                name=push_name,
                phone=phone,
                source=source_text,
                status='novo'
            )
            db.session.add(novo_lead)
        else:
            # Atualiza lead se descobrir campanha depois
            if campaign and getattr(existing_lead, "campaign_id", None) is None:
                existing_lead.campaign_id = campaign.id
            # Atualiza source (mantém mais útil)
            if source_text and getattr(existing_lead, "source", "") != source_text:
                existing_lead.source = source_text

        # Cria novo card
        novo_card = CRMCard(
            clinic_id=clinic_id,
            stage_id=stage.id,
            paciente_nome=push_name,
            paciente_phone=phone,
            historico_conversas=f"{source_text}: {message_text}",
            valor_proposta=0,
            status='open'
        )
        _touch_last_interaction(novo_card)
        db.session.add(novo_card)

        # incrementa leads_count com segurança
        if campaign and hasattr(campaign, "leads_count"):
            campaign.leads_count = (campaign.leads_count or 0) + 1

        db.session.commit()

        return jsonify({
            "status": "processed",
            "clinic_id": clinic_id,
            "campaign": campaign.id if campaign else None,
            "tracking_code": code or None,
            "source": source_text
        }), 200

    except Exception as e:
        logger.exception(f"❌ Erro no webhook WhatsApp: {e}")
        db.session.rollback()
        return jsonify({"status": "error"}), 500
