import os
import requests
import logging
import time
import urllib.parse
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db, WhatsAppContact, MessageLog, Clinic, WhatsAppConnection

bp = Blueprint("marketing_whatsapp", __name__)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES ---
EVOLUTION_API_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "minha-senha-secreta")

startup_cooldown = {} 

def get_headers():
    return {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }

def get_unique_instance_name():
    identity = get_jwt_identity()
    # Prioriza clinic_id para isolamento SaaS
    clinic_id = "1"
    if isinstance(identity, dict):
        clinic_id = str(identity.get("clinic_id") or identity.get("id") or "1")
    return f"clinica_v3_{clinic_id}"

# =========================================================
# 1) ROTA PARA SALVAR O NÚMERO FIXO (A ÂNCORA)
# =========================================================
@bp.route('/whatsapp/settings', methods=['POST'])
@jwt_required()
def save_settings():
    identity = get_jwt_identity()
    clinic_id = identity.get('clinic_id') if isinstance(identity, dict) else 1
    data = request.get_json() or {}
    
    # Limpa o número para salvar apenas dígitos
    raw_phone = data.get('whatsapp_number', '')
    clean_phone = "".join(filter(str.isdigit, raw_phone))
    
    if not clean_phone:
        return jsonify({"ok": False, "message": "Número inválido"}), 400

    clinic = Clinic.query.get(clinic_id)
    if clinic:
        clinic.whatsapp_number = clean_phone
        db.session.commit()
        return jsonify({"ok": True, "message": "Número atualizado!", "number": clean_phone}), 200
    
    return jsonify({"ok": False, "message": "Clínica não encontrada"}), 404

# =========================================================
# 2) GESTÃO DE INSTÂNCIAS (EVOLUTION API)
# =========================================================
def ensure_instance(instance_name):
    try:
        r = requests.get(f"{EVOLUTION_API_URL}/instance/fetchInstances", headers=get_headers(), timeout=10)
        exists = False
        if r.status_code == 200:
            instances = r.json()
            for inst in (instances if isinstance(instances, list) else []):
                if inst.get('instanceName') == instance_name: 
                    exists = True
                    break
        
        if exists: return True 

        # Cria instância se não existir
        payload = {
            "instanceName": instance_name,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS" 
        }
        requests.post(f"{EVOLUTION_API_URL}/instance/create", json=payload, headers=get_headers(), timeout=20)
        return True
            
    except Exception as e:
        logger.error(f"Erro ao garantir instância: {e}")
        return False

# =========================================================
# 3) ROTA DE QR CODE E CONEXÃO
# =========================================================
@bp.route('/whatsapp/qr', methods=['GET'])
@jwt_required()
def get_qr():
    instance_name = get_unique_instance_name()
    ensure_instance(instance_name)

    try:
        # Busca estado da conexão
        state = "close"
        r_state = requests.get(f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}", headers=get_headers(), timeout=10)
        if r_state.status_code == 200:
            state = r_state.json().get('instance', {}).get('state', 'close')

        if state == 'open':
            return jsonify({"status": "connected"}), 200
        
        # Gera novo QR se desconectado
        r_connect = requests.get(f"{EVOLUTION_API_URL}/instance/connect/{instance_name}", headers=get_headers(), timeout=20)
        if r_connect.status_code == 200:
            qr_code = r_connect.json().get('base64')
            return jsonify({"status": "disconnected", "qr_base64": qr_code}), 200

        return jsonify({"status": "disconnected", "message": "Iniciando..."}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# =========================================================
# 4) ROTA DE ENVIO (USANDO NÚMERO FIXO SE DISPONÍVEL)
# =========================================================
@bp.route('/whatsapp/send', methods=['POST'])
@jwt_required()
def send_message():
    instance_name = get_unique_instance_name()
    body = request.get_json(force=True) or {}
    to = "".join(filter(str.isdigit, body.get("to", "")))
    message = body.get("message", "").strip()

    if not to or not message:
        return jsonify({"ok": False, "message": "Dados incompletos"}), 400

    try:
        send_url = f"{EVOLUTION_API_URL}/message/sendText/{instance_name}"
        payload = {"number": to, "text": message, "delay": 1000}
        
        r = requests.post(send_url, json=payload, headers=get_headers(), timeout=30)
        
        # Log da mensagem no banco
        try:
            identity = get_jwt_identity()
            clinic_id = identity.get("clinic_id", 1) if isinstance(identity, dict) else 1
            
            log = MessageLog(
                clinic_id=clinic_id,
                direction="out",
                body=message,
                status="sent" if r.status_code == 201 else "failed"
            )
            db.session.add(log)
            db.session.commit()
        except:
            db.session.rollback()

        if r.status_code == 201:
            return jsonify({"ok": True}), 200
        return jsonify({"ok": False, "error": r.text}), 400

    except Exception as e:
        return jsonify({"ok": False, "message": "Erro de conexão"}), 500

@bp.route('/whatsapp/health', methods=['GET'])
def health():
    return jsonify({"status": "online"}), 200