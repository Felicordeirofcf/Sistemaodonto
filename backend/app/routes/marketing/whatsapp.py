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

# --- AQUI ESTÁ A MUDANÇA PARA DESTRAVAR ---
def get_instance_name(clinic_id):
    # Mudamos o nome para fugir da instância travada "clinica_1"
    # Agora o sistema vai criar "clinica_nova_1" do zero, limpa e sem erros.
    return f"clinica_nova_{clinic_id}"

# --- FUNÇÃO AUXILIAR: DELETAR INSTÂNCIA TRAVADA ---
def force_delete_instance(instance_name):
    try:
        url = f"{EVOLUTION_API_URL}/instance/delete/{instance_name}"
        requests.delete(url, headers=get_headers(), timeout=5)
        logger.warning(f"Instância {instance_name} deletada para limpeza.")
    except Exception as e:
        logger.error(f"Erro ao deletar instância: {e}")

# --- FUNÇÃO: GARANTIR INSTÂNCIA ---
def ensure_instance(clinic_id):
    instance_name = get_instance_name(clinic_id)
    
    # 1. Verifica se existe
    try:
        r = requests.get(f"{EVOLUTION_API_URL}/instance/fetchInstances", headers=get_headers(), timeout=5)
        if r.status_code == 200:
            instances = r.json()
            # Verifica se nosso nome está na lista
            exists = False
            if isinstance(instances, list):
                for inst in instances:
                    if inst.get('name') == instance_name: exists = True
            elif isinstance(instances, dict):
                 if instance_name in instances: exists = True
            
            if exists:
                # Se existe, verifica se está "Close" (travada)
                state_url = f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}"
                r_state = requests.get(state_url, headers=get_headers(), timeout=5)
                if r_state.status_code == 200:
                    state = r_state.json().get('instance', {}).get('state')
                    if state == 'close':
                        # Se está fechada, deleta para recriar do zero
                        logger.info(f"Instância {instance_name} está fechada (CLOSE). Recriando...")
                        force_delete_instance(instance_name)
                        return False # Retorna False para forçar a criação abaixo
                return True

    except Exception as e:
        logger.error(f"Erro ao checar instância: {e}")

    # 2. Se não existe (ou foi deletada), CRIA
    try:
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
        
        logger.error(f"Falha ao criar instância: {r.text}")
        return False
    except Exception as e:
        logger.error(f"Erro fatal ao criar: {e}")
        return False

# --- ROTA: GERAR QR CODE ---
@bp.route('/whatsapp/qr', methods=['GET'])
@jwt_required()
def get_qr():
    identity = get_jwt_identity()
    clinic_id = 1
    if isinstance(identity, dict):
        clinic_id = identity.get("clinic_id", 1)
    
    instance_name = get_instance_name(clinic_id)

    try:
        # Garante que a instância existe
        ensure_instance(clinic_id)

        # Tenta conectar/pegar QR
        connect_url = f"{EVOLUTION_API_URL}/instance/connect/{instance_name}"
        r = requests.get(connect_url, headers=get_headers(), timeout=15)
        
        qr_base64 = None
        status = "disconnected"

        if r.status_code == 200:
            data = r.json()
            # Tenta pegar o base64
            qr_base64 = data.get('base64') or data.get('qrcode', {}).get('base64')
            
            if qr_base64:
                logger.info("QR Code recebido com sucesso!")
                return jsonify({
                    "status": "disconnected", 
                    "qr_base64": qr_base64,
                    "last_update": datetime.utcnow().isoformat()
                }), 200

        # Se não veio QR, checa se já conectou
        state_url = f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}"
        r_state = requests.get(state_url, headers=get_headers(), timeout=5)
        
        if r_state.status_code == 200:
            state_data = r_state.json()
            state = state_data.get('instance', {}).get('state') or state_data.get('state')
            logger.info(f"Estado da instância: {state}")
            
            if state == 'open':
                status = "connected"
            elif state == 'connecting':
                # Se está conectando mas sem QR, espera um pouco
                status = "disconnected" 

        return jsonify({
            "status": status,
            "qr_base64": qr_base64,
            "last_update": datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        logger.exception(f"Erro no fluxo de QR: {e}")
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

    phone_number = ''.join(filter(str.isdigit, to)) 

    try:
        send_url = f"{EVOLUTION_API_URL}/message/sendText/{instance_name}"
        payload = {
            "number": phone_number,
            "options": { "delay": 1200, "presence": "composing" },
            "textMessage": { "text": message }
        }

        r = requests.post(send_url, json=payload, headers=get_headers(), timeout=10)
        
        # Log no banco
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