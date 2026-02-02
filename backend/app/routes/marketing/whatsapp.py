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
    return f"clinica_v3_{clinic_id}"

# --- FUNÇÃO: GARANTIR QUE A INSTÂNCIA EXISTE ---
def ensure_instance(clinic_id):
    instance_name = get_instance_name(clinic_id)
    try:
        r = requests.get(f"{EVOLUTION_API_URL}/instance/fetchInstances", headers=get_headers(), timeout=30)
        if r.status_code == 200:
            instances = r.json()
            if isinstance(instances, list):
                for inst in instances:
                    if inst.get('name') == instance_name: return True
            elif isinstance(instances, dict):
                 if instance_name in instances: return True

        payload = {
            "instanceName": instance_name,
            "token": f"token_{instance_name}",
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS" 
        }
        create_res = requests.post(f"{EVOLUTION_API_URL}/instance/create", json=payload, headers=get_headers(), timeout=40)
        
        if create_res.status_code in [200, 201]:
            # Aplica configurações de performance imediatamente
            settings_payload = {
                "reject_call": True,
                "groupsIgnore": True,
                "alwaysOnline": True,
                "readMessages": True,
                "readStatus": False,
                "syncFullHistory": False
            }
            try:
                requests.post(f"{EVOLUTION_API_URL}/settings/set/{instance_name}", json=settings_payload, headers=get_headers(), timeout=10)
            except:
                pass
            return True
    except Exception as e:
        logger.error(f"Erro instance: {e}")
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
    ensure_instance(clinic_id)

    try:
        qr_code = None
        try:
            r_connect = requests.get(f"{EVOLUTION_API_URL}/instance/connect/{instance_name}", headers=get_headers(), timeout=30)
            if r_connect.status_code == 200:
                data = r_connect.json()
                qr_code = data.get('base64') or data.get('qrcode', {}).get('base64')
        except:
            pass

        state = "close"
        try:
            r_state = requests.get(f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}", headers=get_headers(), timeout=30)
            if r_state.status_code == 200:
                data = r_state.json()
                state = data.get('instance', {}).get('state') or data.get('state')
        except:
            pass

        if state == 'open':
            return jsonify({"status": "connected", "qr_base64": None}), 200
        
        if qr_code:
            return jsonify({"status": "disconnected", "qr_base64": qr_code}), 200

        last_attempt = startup_cooldown.get(instance_name, 0)
        if time.time() - last_attempt < 60:
            return jsonify({"status": "disconnected", "message": "Carregando..."}), 200

        startup_cooldown[instance_name] = time.time()
        requests.get(f"{EVOLUTION_API_URL}/instance/connect/{instance_name}", headers=get_headers(), timeout=40)
        return jsonify({"status": "disconnected", "message": "Iniciando..."}), 200

    except Exception as e:
        logger.error(f"Erro rota QR: {e}")
        return jsonify({"status": "disconnected"}), 200

# --- ROTA: ENVIAR MENSAGEM (CORRIGIDA PARA FORMATO SIMPLES) ---
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
        
        # --- CORREÇÃO AQUI ---
        # A Evolution estava reclamando que faltava a propriedade "text".
        # Vamos enviar no formato simplificado que funciona em todas as versões.
        payload = {
            "number": phone_number,
            "text": message,  # <--- OBRIGATÓRIO NA RAIZ
            "delay": 1200,
            "linkPreview": False
        }

        r = requests.post(send_url, json=payload, headers=get_headers(), timeout=40)
        
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
        logger.error(f"Erro ao enviar: {e}")
        return jsonify({"ok": False, "message": "Timeout ou Erro na API"}), 500

@bp.route('/whatsapp/health', methods=['GET'])
def health():
    return jsonify({"status": "online"}), 200