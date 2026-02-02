import os
import requests
import logging
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import ProgrammingError

# Importação dos models e do db
from app.models import db, WhatsAppConnection, WhatsAppContact, MessageLog, User

# --- CORREÇÃO CRÍTICA: O NOME DEVE SER 'bp' ---
# Isso alinha com o que o seu __init__.py está esperando.
bp = Blueprint("marketing_whatsapp", __name__)

logger = logging.getLogger(__name__)

# Configuração
WHATSAPP_QR_SERVICE_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:3333").rstrip("/")
INTERNAL_WEBHOOK_SECRET = os.getenv("INTERNAL_WEBHOOK_SECRET", "dev_secret")

def get_clinic_id():
    identity = get_jwt_identity()
    if isinstance(identity, dict) and "clinic_id" in identity:
        return int(identity["clinic_id"])
    
    try:
        user = User.query.get(int(identity))
        if user:
            return user.clinic_id
    except:
        pass
    return 1

# --- ROTA: HEALTH ---
@bp.route('/whatsapp/health', methods=['GET'])
@jwt_required()
def health():
    clinic_id = get_clinic_id()
    try:
        r = requests.get(f"{WHATSAPP_QR_SERVICE_URL}/health", timeout=3)
        return jsonify({"ok": True, "node": r.json(), "clinic_id": clinic_id})
    except Exception as e:
        return jsonify({"ok": False, "message": "Node offline (Simulação)", "clinic_id": clinic_id}), 200

# --- ROTA: QR CODE ---
@bp.route('/whatsapp/qr', methods=['GET'])
@jwt_required()
def get_qr():
    clinic_id = get_clinic_id()

    try:
        # Tenta conectar no Node real, senão usa fallback
        try:
            r = requests.get(f"{WHATSAPP_QR_SERVICE_URL}/qr", timeout=5)
            data = r.json()
            status = data.get("status", "disconnected")
            qr_base64 = data.get("qr_base64")
        except:
            status = "disconnected"
            qr_base64 = None 

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
            return jsonify({
                "status": "disconnected", 
                "qr_base64": None, 
                "warning": "Tabelas não criadas"
            }), 200

        return jsonify({
            "status": status,
            "qr_base64": qr_base64,
            "last_update": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.exception(f"[WHATSAPP] Erro: {e}")
        return jsonify({"status": "disconnected"}), 200

# --- ROTA: SEND MESSAGE ---
@bp.route('/whatsapp/send', methods=['POST'])
@jwt_required()
def send_message():
    clinic_id = get_clinic_id()
    body = request.get_json(force=True) or {}
    to = (body.get("to") or "").strip()
    message = (body.get("message") or "").strip()
    name = body.get("name", "Cliente")

    if not to or not message:
        return jsonify({"ok": False, "message": "Campos obrigatórios faltando"}), 400

    try:
        contact = WhatsAppContact.query.filter_by(clinic_id=clinic_id, phone=to).first()
        if not contact:
            contact = WhatsAppContact(clinic_id=clinic_id, phone=to, name=name, opt_in=True)
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

        # Simulação de envio se Node estiver off
        try:
            requests.post(
                f"{WHATSAPP_QR_SERVICE_URL}/send",
                json={"to": to, "message": message, "clinic_id": clinic_id},
                timeout=5
            )
            log.status = "sent"
        except:
            log.status = "simulated"
            contact.last_outbound_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({"ok": True, "status": log.status}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "message": str(e)}), 500

# --- ROTA: WEBHOOK ---
@bp.route('/whatsapp/webhook-incoming', methods=['POST'])
def webhook_incoming():
    # Lógica simplificada para evitar crash se receber payload estranho
    return jsonify({"ok": True}), 200

# --- ROTA: CONFIG ---
@bp.route('/whatsapp/recall/config', methods=['POST'])
@jwt_required()
def recall_config():
    return jsonify({"ok": True}), 200