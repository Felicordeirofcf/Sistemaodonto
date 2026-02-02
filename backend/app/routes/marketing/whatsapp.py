# backend/app/routes/marketing/whatsapp.py
import os
import requests
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import WhatsAppConnection, WhatsAppContact, MessageLog

bp = Blueprint("marketing_whatsapp", __name__)

WHATSAPP_QR_SERVICE_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:3333")
INTERNAL_WEBHOOK_SECRET = os.getenv("INTERNAL_WEBHOOK_SECRET", "dev_secret")


def get_clinic_id_from_jwt() -> int:
    """
    Compatível com:
    - identity dict: {"id":.., "clinic_id":.., ...}
    - identity int/string (fallback)
    """
    identity = get_jwt_identity()

    if isinstance(identity, dict):
        cid = identity.get("clinic_id")
        if cid:
            return int(cid)

    # fallback (1 clínica / demo)
    return 1


def normalize_phone(phone: str) -> str:
    """
    MVP: só remove espaços. (Você pode evoluir pra E.164 depois.)
    """
    return (phone or "").strip().replace(" ", "")


@bp.get("/marketing/whatsapp/qr")
@jwt_required()
def get_qr():
    clinic_id = get_clinic_id_from_jwt()

    try:
        r = requests.get(f"{WHATSAPP_QR_SERVICE_URL}/qr", timeout=8)
        data = r.json()

        status = data.get("status", "disconnected")
        qr_base64 = data.get("qr_base64")

        conn = WhatsAppConnection.query.filter_by(clinic_id=clinic_id).first()
        if not conn:
            conn = WhatsAppConnection(clinic_id=clinic_id, provider="qr")
            db.session.add(conn)

        # preserva configs anteriores no session_data
        sd = conn.session_data or {}
        sd.update({"provider": "qr", "last_qr": bool(qr_base64)})
        conn.session_data = sd
        conn.status = status
        db.session.commit()

        return jsonify({
            "status": status,
            "qr_base64": qr_base64,
            "last_update": datetime.utcnow().isoformat()
        }), 200

    except Exception:
        # se provider cair, não quebra o painel
        return jsonify({"status": "disconnected"}), 200


@bp.post("/marketing/whatsapp/send")
@jwt_required()
def send_message():
    clinic_id = get_clinic_id_from_jwt()
    body = request.get_json(force=True)

    to = normalize_phone(body.get("to"))
    message = (body.get("message") or "").strip()

    if not to or not message:
        return jsonify({"ok": False, "message": "to e message são obrigatórios"}), 400

    # upsert contato
    contact = WhatsAppContact.query.filter_by(clinic_id=clinic_id, phone=to).first()
    if not contact:
        contact = WhatsAppContact(clinic_id=clinic_id, phone=to, opt_in=True)
        db.session.add(contact)
        db.session.commit()

    # bloqueia envio se opt-out
    if contact.opt_out_at is not None or contact.opt_in is False:
        return jsonify({"ok": False, "message": "Contato opt-out (bloqueado)"}), 403

    # log queued
    log = MessageLog(
        clinic_id=clinic_id,
        contact_id=contact.id,
        direction="out",
        body=message,
        status="queued"
    )
    db.session.add(log)
    db.session.commit()

    try:
        r = requests.post(
            f"{WHATSAPP_QR_SERVICE_URL}/send",
            json={"to": to, "message": message, "clinic_id": clinic_id},
            timeout=12
        )
        data = r.json()

        if data.get("ok"):
            log.status = "sent"
            contact.last_outbound_at = datetime.utcnow()
            db.session.commit()
            return jsonify({"ok": True}), 200

        log.status = "failed"
        db.session.commit()
        return jsonify({"ok": False, "message": data.get("message", "Falha no provider")}), 400

    except Exception:
        log.status = "failed"
        db.session.commit()
        return jsonify({"ok": False, "message": "Provider indisponível"}), 500


@bp.post("/marketing/whatsapp/webhook-incoming")
def webhook_incoming():
    """
    Webhook chamado pelo serviço Node (QR) quando chega mensagem.
    Protegido por secret interno.
    """
    secret = request.headers.get("X-Internal-Secret")
    if secret != INTERNAL_WEBHOOK_SECRET:
        return jsonify({"ok": False, "message": "unauthorized"}), 401

    payload = request.get_json(force=True)
    clinic_id = int(payload.get("clinic_id") or 1)
    from_phone = normalize_phone(payload.get("from"))
    text = (payload.get("body") or "").strip()

    if not from_phone or not text:
        return jsonify({"ok": False, "message": "payload inválido"}), 400

    # upsert contato
    contact = WhatsAppContact.query.filter_by(clinic_id=clinic_id, phone=from_phone).first()
    if not contact:
        contact = WhatsAppContact(clinic_id=clinic_id, phone=from_phone, opt_in=True)
        db.session.add(contact)
        db.session.commit()

    contact.last_inbound_at = datetime.utcnow()

    # opt-out simples por palavra-chave
    lowered = text.lower().strip()
    if lowered in ("parar", "stop", "cancelar", "sair"):
        contact.opt_in = False
        contact.opt_out_at = datetime.utcnow()

    log = MessageLog(
        clinic_id=clinic_id,
        contact_id=contact.id,
        direction="in",
        body=text,
        status="sent"
    )
    db.session.add(log)
    db.session.commit()

    # MVP: no próximo passo a gente pluga o motor "Recepcionista"
    return jsonify({"ok": True}), 200


@bp.post("/marketing/whatsapp/recall/config")
@jwt_required()
def recall_config():
    clinic_id = get_clinic_id_from_jwt()
    data = request.get_json(force=True)

    days = int(data.get("days", 30))
    hour = str(data.get("hour", "09:00"))

    conn = WhatsAppConnection.query.filter_by(clinic_id=clinic_id).first()
    if not conn:
        conn = WhatsAppConnection(clinic_id=clinic_id, provider="qr")
        db.session.add(conn)

    sd = conn.session_data or {}
    sd["recall_days"] = days
    sd["recall_hour"] = hour
    conn.session_data = sd

    db.session.commit()
    return jsonify({"ok": True}), 200


@bp.post("/marketing/whatsapp/recall/run")
def recall_run():
    """
    Endpoint para Cron Job do Render rodar 1x por dia.
    Protegido por secret interno.
    """
    secret = request.headers.get("X-Internal-Secret")
    if secret != INTERNAL_WEBHOOK_SECRET:
        return jsonify({"ok": False, "message": "unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    clinic_id = int(payload.get("clinic_id") or 1)

    conn = WhatsAppConnection.query.filter_by(clinic_id=clinic_id).first()
    sd = (conn.session_data or {}) if conn else {}
    recall_days = int(sd.get("recall_days", 30))

    cutoff = datetime.utcnow() - timedelta(days=recall_days)

    # contato elegível:
    # - opt_in true
    # - sem opt-out
    # - não interagiu há X dias (last_inbound_at)
    contacts = WhatsAppContact.query.filter(
        WhatsAppContact.clinic_id == clinic_id,
        WhatsAppContact.opt_in == True,
        WhatsAppContact.opt_out_at.is_(None),
        (WhatsAppContact.last_inbound_at.is_(None) | (WhatsAppContact.last_inbound_at < cutoff))
    ).limit(50).all()

    sent = 0
    failed = 0

    for c in contacts:
        text = (
            "Olá! Aqui é a recepção 😊\n"
            "Passando para saber como você está e se deseja agendar um retorno/limpeza.\n"
            "Quer que eu veja horários disponíveis?"
        )

        # log queued
        log = MessageLog(
            clinic_id=clinic_id,
            contact_id=c.id,
            direction="out",
            body=text,
            status="queued"
        )
        db.session.add(log)
        db.session.commit()

        try:
            r = requests.post(
                f"{WHATSAPP_QR_SERVICE_URL}/send",
                json={"to": c.phone, "message": text, "clinic_id": clinic_id},
                timeout=12
            )
            data = r.json()

            if data.get("ok"):
                log.status = "sent"
                c.last_outbound_at = datetime.utcnow()
                sent += 1
            else:
                log.status = "failed"
                failed += 1

            db.session.commit()

        except Exception:
            log.status = "failed"
            db.session.commit()
            failed += 1

    return jsonify({"ok": True, "sent": sent, "failed": failed, "count": len(contacts)}), 200
