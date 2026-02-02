# backend/app/routes/marketing/whatsapp.py
import os
import requests
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import ProgrammingError

from app import db
from app.models import WhatsAppConnection, WhatsAppContact, MessageLog

bp = Blueprint("marketing_whatsapp", __name__)

WHATSAPP_QR_SERVICE_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:3333").rstrip("/")
INTERNAL_WEBHOOK_SECRET = os.getenv("INTERNAL_WEBHOOK_SECRET", "dev_secret")

def get_clinic_id():
    identity = get_jwt_identity()
    if isinstance(identity, dict) and "clinic_id" in identity:
        return int(identity["clinic_id"])
    # fallback 1 clinica
    return int(os.getenv("CLINIC_ID", "1"))


@bp.get("/api/marketing/whatsapp/health")
@jwt_required()
def health():
    clinic_id = get_clinic_id()
    try:
        r = requests.get(f"{WHATSAPP_QR_SERVICE_URL}/health", timeout=8)
        return jsonify({"ok": True, "node": r.json(), "clinic_id": clinic_id})
    except Exception as e:
        return jsonify({"ok": False, "message": f"Falha ao chamar node: {e}", "clinic_id": clinic_id}), 200


@bp.get("/api/marketing/whatsapp/qr")
@jwt_required()
def get_qr():
    clinic_id = get_clinic_id()

    try:
        r = requests.get(f"{WHATSAPP_QR_SERVICE_URL}/qr", timeout=10)
        data = r.json()
        status = data.get("status", "disconnected")
        qr_base64 = data.get("qr_base64")

        # tenta salvar status no db (mas não quebra se tabela não existir ainda)
        try:
            conn = WhatsAppConnection.query.filter_by(clinic_id=clinic_id).first()
            if not conn:
                conn = WhatsAppConnection(clinic_id=clinic_id, provider="qr")
                db.session.add(conn)

            conn.status = status
            conn.session_data = {"provider": "qr", "last_qr": bool(qr_base64)}
            db.session.commit()
        except ProgrammingError:
            db.session.rollback()
            # tabelas ainda não existem (migrations não rodaram)
            return jsonify({
                "status": status,
                "qr_base64": qr_base64,
                "last_update": datetime.utcnow().isoformat(),
                "warning": "Tabelas WhatsApp ainda não existem. Rode migrations (flask db upgrade)."
            }), 200

        return jsonify({
            "status": status,
            "qr_base64": qr_base64,
            "last_update": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        current_app.logger.exception(f"[WHATSAPP][QR] erro chamando node: {e}")
        return jsonify({"status": "disconnected"}), 200


@bp.post("/api/marketing/whatsapp/send")
@jwt_required()
def send_message():
    clinic_id = get_clinic_id()
    body = request.get_json(force=True) or {}
    to = (body.get("to") or "").strip()
    message = (body.get("message") or "").strip()

    if not to or not message:
        return jsonify({"ok": False, "message": "to e message são obrigatórios"}), 400

    # --- DB (vai falhar se você não rodou migration)
    try:
        contact = WhatsAppContact.query.filter_by(clinic_id=clinic_id, phone=to).first()
    except ProgrammingError:
        db.session.rollback()
        return jsonify({
            "ok": False,
            "message": "Tabelas do WhatsApp não existem no banco. Rode: flask db upgrade"
        }), 500

    if not contact:
        contact = WhatsAppContact(clinic_id=clinic_id, phone=to, opt_in=True)
        db.session.add(contact)
        db.session.commit()

    log = MessageLog(
        clinic_id=clinic_id,
        contact_id=contact.id,
        direction="out",
        body=message,
        status="queued"
    )
    db.session.add(log)
    db.session.commit()

    # --- chama o Node
    try:
        r = requests.post(
            f"{WHATSAPP_QR_SERVICE_URL}/send",
            json={"to": to, "message": message, "clinic_id": clinic_id},
            timeout=15
        )
        data = r.json()

        if r.ok and data.get("ok"):
            log.status = "sent"
            contact.last_outbound_at = datetime.utcnow()
            db.session.commit()
            return jsonify({"ok": True}), 200

        log.status = "failed"
        db.session.commit()
        return jsonify({"ok": False, "message": data.get("message", "Falha no provider")}), 400

    except Exception as e:
        current_app.logger.exception(f"[WHATSAPP][SEND] provider indisponível: {e}")
        log.status = "failed"
        db.session.commit()
        return jsonify({"ok": False, "message": "Provider indisponível"}), 500


@bp.post("/api/marketing/whatsapp/webhook-incoming")
def webhook_incoming():
    secret = request.headers.get("X-Internal-Secret")
    if secret != INTERNAL_WEBHOOK_SECRET:
        return jsonify({"ok": False, "message": "unauthorized"}), 401

    payload = request.get_json(force=True) or {}
    clinic_id = int(payload.get("clinic_id") or 1)
    from_phone = (payload.get("from") or "").strip()
    text = (payload.get("body") or "").strip()

    if not from_phone or not text:
        return jsonify({"ok": False, "message": "payload inválido"}), 400

    # se não tiver tabelas ainda, não quebra o node
    try:
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

    except ProgrammingError:
        db.session.rollback()
        return jsonify({"ok": True, "warning": "Tabelas WhatsApp ainda não criadas"}), 200

    return jsonify({"ok": True}), 200


@bp.post("/api/marketing/whatsapp/recall/config")
@jwt_required()
def recall_config():
    clinic_id = get_clinic_id()
    data = request.get_json(force=True) or {}
    days = int(data.get("days", 30))
    hour = str(data.get("hour", "09:00"))

    try:
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

    except ProgrammingError:
        db.session.rollback()
        return jsonify({"ok": False, "message": "Tabelas WhatsApp não existem. Rode: flask db upgrade"}), 500
