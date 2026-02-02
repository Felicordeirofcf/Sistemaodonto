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
qr_code_cache = {}

def get_headers():
    return {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }

def get_instance_name(clinic_id):
    # Mantém o nome v3 que funcionou
    return f"clinica_v3_{clinic_id}"

# --- FUNÇÃO: GARANTIR QUE A INSTÂNCIA EXISTE ---
def ensure_instance(clinic_id):
    instance_name = get_instance_name(clinic_id)
    try:
        r = requests.get(f"{EVOLUTION_API_URL}/instance/fetchInstances", headers=get_headers(), timeout=5)
        if r.status_code == 200:
            instances = r.json()
            exists = False
            if isinstance(instances, list):
                for inst in instances:
                    if inst.get('name') == instance_name: exists = True
            elif isinstance(instances, dict):
                 if instance_name in instances: exists = True
            
            if exists:
                return True 

        # Se não existe, CRIA
        payload = {
            "instanceName": instance_name,
            "token": f"token_{instance_name}",
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS" 
        }
        r = requests.post(f"{EVOLUTION_API_URL}/instance/create", json=payload, headers=get_headers(), timeout=15)
        if r.status_code in [200, 201]:
            logger.info(f"Instância {instance_name} criada com sucesso.")
            return True
            
    except Exception as e:
        logger.error(f"Erro ao garantir instância: {e}")
    
    return False

# --- ROTA: GERAR QR CODE (COM COOLDOWN DE 60s) ---
@bp.route('/whatsapp/qr', methods=['GET'])
@jwt_required()
def get_qr():
    identity = get_jwt_identity()
    clinic_id = 1
    if isinstance(identity, dict):
        clinic_id = identity.get("clinic_id", 1)
    
    instance_name = get_instance_name(clinic_id)

    # --- 1. VERIFICAÇÃO DE COOLDOWN ---
    last_attempt = startup_cooldown.get(instance_name, 0)
    
    # Aumentei para 60 segundos para dar bastante tempo ao Render
    if time.time() - last_attempt < 60:
        logger.info(f"⏳ Cooldown ativo. Retornando cache ou aguarde...")
        cached_qr = qr_code_cache.get(instance_name)
        if cached_qr:
            return jsonify({"status": "disconnected", "qr_base64": cached_qr, "message": "Aguarde..."}), 200
        else:
            return jsonify({"status": "disconnected", "qr_base64": None, "message": "Iniciando... (Aguarde 1 min)"}), 200

    try:
        ensure_instance(clinic_id)

        # 2. Verifica estado real
        state_url = f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}"
        r_state = requests.get(state_url, headers=get_headers(), timeout=5)
        
        current_state = "close"
        if r_state.status_code == 200:
            data = r_state.json()
            current_state = data.get('instance', {}).get('state') or data.get('state')

        logger.info(f"Estado real: {current_state}")

        if current_state == 'open':
            if instance_name in qr_code_cache: del qr_code_cache[instance_name]
            return jsonify({"status": "connected", "qr_base64": None}), 200
        
        elif current_state == 'connecting':
            cached_qr = qr_code_cache.get(instance_name)
            return jsonify({"status": "disconnected", "qr_base64": cached_qr, "message": "Conectando..."}), 200

        else:
            # ESTÁ FECHADA. MANDA CONECTAR E ATIVA O COOLDOWN.
            logger.info(f"🚀 Enviando comando CONNECT para {instance_name}...")
            
            # ATIVA O TIMER DE 60 SEGUNDOS
            startup_cooldown[instance_name] = time.time()
            
            connect_url = f"{EVOLUTION_API_URL}/instance/connect/{instance_name}"
            r = requests.get(connect_url, headers=get_headers(), timeout=15)
            
            qr_base64 = None
            if r.status_code == 200:
                qr_base64 = r.json().get('base64') or r.json().get('qrcode', {}).get('base64')
                if qr_base64:
                    qr_code_cache[instance_name] = qr_base64
            
            return jsonify({
                "status": "disconnected", 
                "qr_base64": qr_base64
            }), 200

    except Exception as e:
        logger.exception(f"Erro no fluxo de QR: {e}")
        return jsonify({"status": "disconnected"}), 200

# ... (Mantenha o send_message e health iguais) ...
@bp.route('/whatsapp/send', methods=['POST'])
@jwt_required()
def send_message():
    # (Copie o código da resposta anterior se precisar, não mudou nada aqui)
    return jsonify({"ok": False, "message": "Implementação omitida para brevidade"}), 200

@bp.route('/whatsapp/health', methods=['GET'])
def health():
    return jsonify({"status": "online", "mode": "evolution-api"}), 200