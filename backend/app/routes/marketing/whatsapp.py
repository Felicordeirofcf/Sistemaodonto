import os
import requests
import logging
import time
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db, WhatsAppContact, MessageLog

bp = Blueprint("marketing_whatsapp", __name__)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES ---
EVOLUTION_API_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "minha-senha-secreta")

# --- MEMÓRIA TEMPORÁRIA ---
startup_cooldown = {} 

def get_headers():
    return {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }

def get_instance_name(clinic_id):
    # Mantemos o nome v3 que já funcionou no log!
    return f"clinica_v3_{clinic_id}"

def ensure_instance(clinic_id):
    instance_name = get_instance_name(clinic_id)
    try:
        r = requests.get(f"{EVOLUTION_API_URL}/instance/fetchInstances", headers=get_headers(), timeout=5)
        if r.status_code == 200:
            instances = r.json()
            if isinstance(instances, list):
                for inst in instances:
                    if inst.get('name') == instance_name: return True
            elif isinstance(instances, dict):
                 if instance_name in instances: return True

        # Se não existe, CRIA
        payload = {
            "instanceName": instance_name,
            "token": f"token_{instance_name}",
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS" 
        }
        requests.post(f"{EVOLUTION_API_URL}/instance/create", json=payload, headers=get_headers(), timeout=15)
        return True
    except Exception as e:
        logger.error(f"Erro instance: {e}")
        return False

# --- ROTA: GERAR QR CODE (LÓGICA CORRIGIDA) ---
@bp.route('/whatsapp/qr', methods=['GET'])
@jwt_required()
def get_qr():
    identity = get_jwt_identity()
    clinic_id = 1
    if isinstance(identity, dict):
        clinic_id = identity.get("clinic_id", 1)
    
    instance_name = get_instance_name(clinic_id)
    ensure_instance(clinic_id)

    try:
        # 1. TENTA PEGAR O QR CODE DIRETO (SEMPRE)
        # Mesmo se estiver no tempo de espera, se o QR existe, mostre ele!
        qr_code = None
        try:
            r_connect = requests.get(f"{EVOLUTION_API_URL}/instance/connect/{instance_name}", headers=get_headers(), timeout=5)
            if r_connect.status_code == 200:
                data = r_connect.json()
                qr_code = data.get('base64') or data.get('qrcode', {}).get('base64')
        except:
            pass

        # 2. VERIFICA ESTADO
        state = "close"
        try:
            r_state = requests.get(f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}", headers=get_headers(), timeout=5)
            if r_state.status_code == 200:
                data = r_state.json()
                state = data.get('instance', {}).get('state') or data.get('state')
        except:
            pass

        # 3. DECISÃO
        if state == 'open':
            return jsonify({"status": "connected", "qr_base64": None}), 200
        
        # Se achamos o QR Code no passo 1, retorna ele AGORA!
        if qr_code:
            return jsonify({"status": "disconnected", "qr_base64": qr_code}), 200

        # 4. SÓ SE NÃO TIVER QR CODE AINDA: VERIFICA O COOLDOWN
        last_attempt = startup_cooldown.get(instance_name, 0)
        if time.time() - last_attempt < 60:
            return jsonify({"status": "disconnected", "message": "Carregando..."}), 200

        # Se passou do tempo e não tem QR code, manda conectar de novo
        startup_cooldown[instance_name] = time.time()
        requests.get(f"{EVOLUTION_API_URL}/instance/connect/{instance_name}", headers=get_headers(), timeout=10)
        
        return jsonify({"status": "disconnected", "message": "Iniciando..."}), 200

    except Exception as e:
        logger.error(f"Erro rota QR: {e}")
        return jsonify({"status": "disconnected"}), 200

# ... (Mantenha o resto igual) ...
@bp.route('/whatsapp/send', methods=['POST'])
@jwt_required()
def send_message():
    # ... (código de envio padrão) ...
    return jsonify({"ok": False}), 200

@bp.route('/whatsapp/health', methods=['GET'])
def health():
    return jsonify({"status": "online"}), 200