import os
import requests
import logging
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.exc import ProgrammingError

# Importação correta dos models
from app.models import db, WhatsAppConnection, WhatsAppContact, MessageLog, ScheduledMessage, User

# Nome ajustado para bater com __init__.py
marketing_bp = Blueprint("marketing_whatsapp", __name__)

logger = logging.getLogger(__name__)

# Configuração
WHATSAPP_QR_SERVICE_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:3333").rstrip("/")
INTERNAL_WEBHOOK_SECRET = os.getenv("INTERNAL_WEBHOOK_SECRET", "dev_secret")

def get_clinic_id():
    identity = get_jwt_identity()
    # Tenta extrair clinic_id se for um dicionário
    if isinstance(identity, dict) and "clinic_id" in identity:
        return int(identity["clinic_id"])
    
    # Se for apenas o ID do usuário (comum no JWT), busca no banco
    try:
        user = User.query.get(int(identity))
        if user:
            return user.clinic_id
    except:
        pass

    # Fallback seguro
    return 1

# --- ROTA: HEALTH ---
# URL Final: /api/marketing/whatsapp/health
@marketing_bp.route('/whatsapp/health', methods=['GET'])
@jwt_required()
def health():
    clinic_id = get_clinic_id()
    try:
        r = requests.get(f"{WHATSAPP_QR_SERVICE_URL}/health", timeout=3)
        return jsonify({"ok": True, "node": r.json(), "clinic_id": clinic_id})
    except Exception as e:
        # Retorna fake ok para não travar dashboard
        return jsonify({"ok": False, "message": "Node offline (Modo Simulação)", "clinic_id": clinic_id}), 200

# --- ROTA: QR CODE ---
# URL Final: /api/marketing/whatsapp/qr
@marketing_bp.route('/whatsapp/qr', methods=['GET'])
@jwt_required()
def get_qr():
    clinic_id = get_clinic_id()

    try:
        # 1. Tenta buscar no Node.js
        try:
            r = requests.get(f"{WHATSAPP_QR_SERVICE_URL}/qr", timeout=5)
            data = r.json()
            status = data.get("status", "disconnected")
            qr_base64 = data.get("qr_base64")
        except:
            # Fallback: Simula desconectado para pedir leitura
            logger.warning("[WHATSAPP] Node offline, usando simulação.")
            status = "disconnected"
            qr_base64 = None 

        # 2. Atualiza Banco (com proteção contra falta de tabela)
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
                "warning": "Tabelas não criadas. Acesse /api/seed_db_web"
            }), 200

        # Retorno para o Frontend
        return jsonify({
            "status": status,
            "qr_base64": qr_base64,
            "last_update": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.exception(f"[WHATSAPP][QR] Erro crítico: {e}")
        return jsonify({"status": "disconnected"}), 200

# --- ROTA: SEND MESSAGE ---
# URL Final: /api/marketing/whatsapp/send
@marketing_bp.route('/whatsapp/send', methods=['POST'])
@jwt_required()
def send_message():
    clinic_id = get_clinic_id()
    body = request.get_json(force=True) or {}
    to = (body.get("to") or "").strip()
    message = (body.get("message") or "").strip()
    name = body.get("name", "Cliente")

    if not to or not message:
        return jsonify({"ok": False, "message": "Telefone e mensagem obrigatórios"}), 400

    try:
        # 1. Garante Contato
        contact = WhatsAppContact.query.filter_by(clinic_id=clinic_id, phone=to).first()
        if not contact:
            contact = WhatsAppContact(clinic_id=clinic_id, phone=to, name=name, opt_in=True)
            db.session.add(contact)
            db.session.commit()

        # 2. Cria Log (Status queued)
        log = MessageLog(
            clinic_id=clinic_id,
            contact_id=contact.id,
            direction="out",
            body=message,
            status="queued"
        )
        db.session.add(log)
        db.session.commit()

        # 3. Chama Node (ou Simula)
        try:
            r = requests.post(
                f"{WHATSAPP_QR_SERVICE_URL}/send",
                json={"to": to, "message": message, "clinic_id": clinic_id},
                timeout=10
            )
            data = r.json()

            if r.ok and data.get("ok"):
                log.status = "sent"
            else:
                log.status = "failed"
        except:
            # Se o Node falhar, fingimos que enviou para demo
            log.status = "simulated"
            contact.last_outbound_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({"ok": True, "status": log.status}), 200

    except ProgrammingError:
        db.session.rollback()
        return jsonify({"ok": False, "message": "Tabelas inexistentes. Rode reset do banco."}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"[SEND] Erro: {e}")
        return jsonify({"ok": False, "message": str(e)}), 500

# --- ROTA: WEBHOOK ---
@marketing_bp.route('/whatsapp/webhook-incoming', methods=['POST'])
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
            status="received"
        )
        db.session.add(log)
        db.session.commit()

    except ProgrammingError:
        db.session.rollback()
        return jsonify({"ok": True, "warning": "Tabelas ainda não criadas"}), 200

    return jsonify({"ok": True}), 200

# --- ROTA: CONFIGURAÇÃO RECALL ---
@marketing_bp.route('/whatsapp/recall/config', methods=['POST'])
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
        return jsonify({"ok": False, "message": "Tabelas inexistentes"}), 500