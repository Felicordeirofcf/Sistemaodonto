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

def get_headers():
    return {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }

def get_instance_name(clinic_id):
    # Nome final para encerrar a novela
    return f"clinica_final_{clinic_id}"

# --- FUNÇÃO: CHECAR E CRIAR INSTÂNCIA ---
def ensure_instance(clinic_id):
    instance_name = get_instance_name(clinic_id)
    try:
        # Verifica se existe
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
                return True # Já existe, tudo certo.

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

# --- ROTA: GERAR QR CODE (COM PROTEÇÃO ANTI-LOOP) ---
@bp.route('/whatsapp/qr', methods=['GET'])
@jwt_required()
def get_qr():
    identity = get_jwt_identity()
    clinic_id = 1
    if isinstance(identity, dict):
        clinic_id = identity.get("clinic_id", 1)
    
    instance_name = get_instance_name(clinic_id)

    try:
        ensure_instance(clinic_id)

        # 1. PRIMEIRO: Verifica o estado ATUAL antes de mandar conectar
        state_url = f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}"
        r_state = requests.get(state_url, headers=get_headers(), timeout=5)
        
        current_state = "close"
        if r_state.status_code == 200:
            data = r_state.json()
            current_state = data.get('instance', {}).get('state') or data.get('state')

        logger.info(f"Estado atual da instância: {current_state}")

        # 2. DECISÃO INTELIGENTE
        if current_state == 'open':
            return jsonify({"status": "connected", "qr_base64": None}), 200
            
        elif current_state == 'connecting':
            # SE JÁ ESTÁ CONECTANDO, NÃO FAZ NADA! Só espera.
            # Tenta buscar o QR Code se já tiver sido gerado
            connect_url = f"{EVOLUTION_API_URL}/instance/connect/{instance_name}"
            r_qr = requests.get(connect_url, headers=get_headers(), timeout=10)
            qr_base64 = None
            if r_qr.status_code == 200:
                qr_base64 = r_qr.json().get('base64')
            
            return jsonify({
                "status": "disconnected", 
                "qr_base64": qr_base64, # Pode ser null se ainda estiver carregando
                "message": "Iniciando..."
            }), 200

        else:
            # SÓ MANDA CONECTAR SE ESTIVER FECHADO (CLOSE)
            connect_url = f"{EVOLUTION_API_URL}/instance/connect/{instance_name}"
            r = requests.get(connect_url, headers=get_headers(), timeout=15)
            
            qr_base64 = None
            if r.status_code == 200:
                qr_base64 = r.json().get('base64')
            
            return jsonify({
                "status": "disconnected", 
                "qr_base64": qr_base64
            }), 200

    except Exception as e:
        logger.exception(f"Erro no fluxo de QR: {e}")
        return jsonify({"status": "disconnected"}), 200

# --- ROTA: ENVIAR MENSAGEM ---
@bp.route('/whatsapp/send', methods=['POST'])
@jwt_required()
def send_message():
    # ... (Mantenha o código de envio igual, ele não causa problemas)
    # Vou replicar aqui para facilitar o copy-paste completo
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

    phone_number = ''.join(filter(str.isdigit, to)) 

    try:
        send_url = f"{EVOLUTION_API_URL}/message/sendText/{instance_name}"
        payload = {
            "number": phone_number,
            "options": { "delay": 1200, "presence": "composing" },
            "textMessage": { "text": message }
        }

        r = requests.post(send_url, json=payload, headers=get_headers(), timeout=10)
        
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
        except:
            db.session.rollback()

        if r.status_code == 201:
            return jsonify({"ok": True, "status": "sent"}), 200
        else:
            return jsonify({"ok": False, "message": f"Erro Evolution: {r.text}"}), 400

    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500

@bp.route('/whatsapp/health', methods=['GET'])
def health():
    return jsonify({"status": "online", "mode": "evolution-api"}), 200