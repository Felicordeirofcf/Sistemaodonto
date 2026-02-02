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

def get_clinic_id():
    """
    Ajuste aqui para o seu multi-tenant.
    Se seu jwt_identity já carrega clinic_id, use isso.
    """
    identity = get_jwt_identity()
    # exemplo comum:
    if isinstance(identity, dict) and "clinic_id" in identity:
        return int(identity["clinic_id"])
    # fallback (1 clínica)
    return 1

@bp.get("/api/marketing/whatsapp/qr")
@jwt_required()
def get_qr():
    clinic_id = get_clinic_id()

    # tenta buscar status/qr do serviço node
    try:
        r = requests.get(f"{WHATSAPP_QR_SERVICE_URL}/qr", timeout=8)
        data = r.json()
        status = data.get("status", "disconnected")
        qr_base64 = data.get("qr_base64")

        # salva status em db
        conn = WhatsAppConnection.query.filter_by(clinic_id=clinic_id).first()
        if not conn:
            conn = WhatsAppConnection(clinic_id=clinic_id, provider="qr")
            db.session.add(conn)

        conn.status = status
        conn.session_data = {"provider": "qr", "last_qr": bool(qr_base64)}
        db.session.commit()

        return jsonify({
            "status": status,
            "qr_base64": qr_base64,
            "last_update": datetime.utcnow().isoformat()
        })
    except Exception:
        return jsonify({"status": "disconnected"}), 200


@bp.post("/api/marketing/whatsapp/send")
@jwt_required()
def send_message():
    clinic_id = get_clinic_id()
    body = request.get_json(force=True)
    to = (body.get("to") or "").strip()
    message = (body.get("message") or "").strip()

    if not to or not message:
        return jsonify({"ok": False, "message": "to e message são obrigatórios"}), 400

    # upsert contato
    contact = WhatsAppContact.query.filter_by(clinic_id=clinic_id, phone=to).first()
    if not contact:
        contact = WhatsAppContact(clinic_id=clinic_id, phone=to, opt_in=True)
        db.session.add(contact)
        db.session.commit()

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
            return jsonify({"ok": True})
        else:
            log.status = "failed"
            db.session.commit()
            return jsonify({"ok": False, "message": data.get("message", "Falha no provider")}), 400
    except Exception:
        log.status = "failed"
        db.session.commit()
        return jsonify({"ok": False, "message": "Provider indisponível"}), 500


@bp.post("/api/marketing/whatsapp/webhook-incoming")
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
    from_phone = (payload.get("from") or "").strip()
    text = (payload.get("body") or "").strip()

    if not from_phone or not text:
        return jsonify({"ok": False}), 400

    contact = WhatsAppContact.query.filter_by(clinic_id=clinic_id, phone=from_phone).first()
    if not contact:
        contact = WhatsAppContact(clinic_id=clinic_id, phone=from_phone, opt_in=True)
        db.session.add(contact)
        db.session.commit()

    contact.last_inbound_at = datetime.utcnow()

    log = MessageLog(
        clinic_id=clinic_id,
        contact_id=contact.id,
        direction="in",
        body=text,
        status="sent"
    )
    db.session.add(log)
    db.session.commit()

    # MVP: aqui depois plugamos o "motor recepcionista"
    return jsonify({"ok": True})


# Config de recall: salva em DB simples (1 clínica), ou pode virar tabela
@bp.post("/api/marketing/whatsapp/recall/config")
@jwt_required()
def recall_config():
    clinic_id = get_clinic_id()
    data = request.get_json(force=True)
    days = int(data.get("days", 30))
    hour = str(data.get("hour", "09:00"))

    conn = WhatsAppConnection.query.filter_by(clinic_id=clinic_id).first()
    if not conn:
        conn = WhatsAppConnection(clinic_id=clinic_id, provider="qr")
        db.session.add(conn)

    # guarda config dentro do session_data (MVP)
    sd = conn.session_data or {}
    sd["recall_days"] = days
    sd["recall_hour"] = hour
    conn.session_data = sd
    db.session.commit()

    return jsonify({"ok": True})
