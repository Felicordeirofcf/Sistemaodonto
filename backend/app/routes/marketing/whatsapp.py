import os
import requests
import logging
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db, WhatsAppContact, MessageLog, User

# Nome "bp" para bater com o __init__.py
bp = Blueprint("marketing_whatsapp", __name__)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES ---
# Pega a URL e a Senha que você configurou no Environment do Render
EVOLUTION_API_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "minha-senha-secreta")

def get_headers():
    return {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }

def get_instance_name(clinic_id):
    """Cria um nome único para a instância da clínica (ex: clinica_1)"""
    return f"clinica_{clinic_id}"

# --- FUNÇÃO: GARANTIR QUE A INSTÂNCIA EXISTE NA EVOLUTION ---
def ensure_instance(clinic_id):
    instance_name = get_instance_name(clinic_id)
    
    # 1. Verifica se a instância já existe
    try:
        r = requests.get(f"{EVOLUTION_API_URL}/instance/fetchInstances", headers=get_headers(), timeout=5)
        if r.status_code == 200:
            instances = r.json()
            # A Evolution v2 pode retornar uma lista ou um dicionário
            if isinstance(instances, list):
                for inst in instances:
                    if inst.get('name') == instance_name: return True
            elif isinstance(instances, dict):
                 if instance_name in instances: return True
    except Exception as e:
        logger.error(f"Erro ao checar instância: {e}")

    # 2. Se não existe, CRIA UMA NOVA
    try:
        payload = {
            "instanceName": instance_name,
            "token": f"token_{instance_name}",
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS" 
        }
        r = requests.post(f"{EVOLUTION_API_URL}/instance/create", json=payload, headers=get_headers(), timeout=10)
        
        if r.status_code in [200, 201]:
            logger.info(f"Instância {instance_name} criada com sucesso.")
            return True
            
        logger.error(f"Falha ao criar instância: {r.text}")
        return False
    except Exception as e:
        logger.error(f"Erro fatal ao criar instância na Evolution: {e}")
        return False

# --- ROTA: GERAR QR CODE ---
@bp.route('/whatsapp/qr', methods=['GET'])
@jwt_required()
def get_qr():
    # Identifica o usuário e a clínica
    identity = get_jwt_identity()
    clinic_id = 1
    if isinstance(identity, dict):
        clinic_id = identity.get("clinic_id", 1)
    
    instance_name = get_instance_name(clinic_id)

    try:
        # Passo 1: Garante que a Evolution tem uma instância pronta
        if not ensure_instance(clinic_id):
            return jsonify({"status": "disconnected", "message": "Falha no motor WhatsApp"}), 500

        # Passo 2: Pede o QR Code para a Evolution
        connect_url = f"{EVOLUTION_API_URL}/instance/connect/{instance_name}"
        r = requests.get(connect_url, headers=get_headers(), timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            # A Evolution retorna o base64 do QR Code
            qr_base64 = data.get('base64')
            
            status = "disconnected"
            
            # Se não veio QR Code, verifica se já está CONECTADO
            if not qr_base64:
                state_url = f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}"
                r_state = requests.get(state_url, headers=get_headers())
                if r_state.status_code == 200:
                    state_data = r_state.json()
                    # Verifica o estado real da conexão
                    state = state_data.get('instance', {}).get('state')
                    if state == 'open':
                        status = "connected"
            
            return jsonify({
                "status": status,
                "qr_base64": qr_base64,
                "last_update": datetime.utcnow().isoformat()
            }), 200
            
        return jsonify({"status": "disconnected"}), 200

    except Exception as e:
        logger.exception(f"Erro ao buscar QR Code: {e}")
        return jsonify({"status": "disconnected", "error": str(e)}), 200

# --- ROTA: ENVIAR MENSAGEM ---
@bp.route('/whatsapp/send', methods=['POST'])
@jwt_required()
def send_message():
    identity = get_jwt_identity()
    clinic_id = 1
    if isinstance(identity, dict):
        clinic_id = identity.get("clinic_id", 1)

    instance_name = get_instance_name(clinic_id)
    body = request.get_json(force=True) or {}
    to = (body.get("to") or "").strip()
    message = (body.get("message") or "").strip()

    if not to or not message:
        return jsonify({"ok": False, "message": "Dados incompletos"}), 400

    # Limpa o número (deixa apenas dígitos)
    phone_number = ''.join(filter(str.isdigit, to)) 

    try:
        # Endpoint para enviar texto na Evolution v2
        send_url = f"{EVOLUTION_API_URL}/message/sendText/{instance_name}"
        
        payload = {
            "number": phone_number,
            "options": { "delay": 1200, "presence": "composing" },
            "textMessage": { "text": message }
        }

        r = requests.post(send_url, json=payload, headers=get_headers(), timeout=10)
        
        # Salva o log no banco de dados do sistema
        try:
            contact = WhatsAppContact.query.filter_by(clinic_id=clinic_id, phone=to).first()
            if not contact:
                contact = WhatsAppContact(clinic_id=clinic_id, phone=to, name="Cliente", opt_in=True)
                db.session.add(contact)
            
            log_status = "sent" if r.status_code == 201 else "failed"
            log = MessageLog(
                clinic_id=clinic_id,
                contact_id=contact.id,
                direction="out",
                body=message,
                status=log_status
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()

        if r.status_code == 201:
            return jsonify({"ok": True, "status": "sent"}), 200
        else:
            return jsonify({"ok": False, "message": f"Erro Evolution: {r.text}"}), 400

    except Exception as e:
        logger.error(f"Erro envio Evolution: {e}")
        return jsonify({"ok": False, "message": str(e)}), 500

# --- ROTA: HEALTH CHECK ---
@bp.route('/whatsapp/health', methods=['GET'])
def health():
    return jsonify({"status": "online", "mode": "evolution-api"}), 200