import os
import json
import requests
import logging
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db, WhatsAppContact, MessageLog, Clinic, WhatsAppConnection

bp = Blueprint("marketing_whatsapp", __name__)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES ---
EVOLUTION_API_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")

TIMEOUT_SHORT = 10
TIMEOUT_MED = 20
TIMEOUT_LONG = 30

def get_headers():
    return {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }

def _get_clinic_id_from_jwt() -> int:
    identity = get_jwt_identity()
    # Se a identidade for um dicionário (claims adicionais)
    if isinstance(identity, dict):
        cid = identity.get("clinic_id")
        if cid:
            try:
                return int(cid)
            except Exception:
                pass
    
    # Se a identidade for apenas o ID do usuário (string ou int)
    # Precisamos buscar o usuário no banco para saber a clínica dele
    try:
        from app.models import User
        user = User.query.get(identity)
        if user:
            return user.clinic_id
    except Exception:
        pass
        
    return 1

def get_unique_instance_name(clinic_id: int) -> str:
    return f"clinica_v3_{clinic_id}"

def _digits_only(s: str) -> str:
    return "".join([c for c in (s or "") if c.isdigit()])

def _normalize_phone_from_jid(jid: str) -> str:
    if not jid or not isinstance(jid, str):
        return ""
    base = jid.split("@")[0]
    base = base.split(":")[0]
    return _digits_only(base)

def _safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return None

def _fetch_instances():
    url = f"{EVOLUTION_API_URL}/instance/fetchInstances"
    try:
        r = requests.get(url, headers=get_headers(), timeout=TIMEOUT_SHORT)
        data = _safe_json(r)
        if r.status_code != 200 or data is None:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("instances", "data", "response"):
                if isinstance(data.get(key), list):
                    return data.get(key)
        return []
    except Exception:
        return []

def _find_instance(instance_name: str):
    instances = _fetch_instances()
    for inst in instances:
        if not isinstance(inst, dict):
            continue
        name = inst.get("instanceName") or inst.get("name") or inst.get("instance") or ""
        if name == instance_name:
            return inst
    return None

def _extract_owner_from_instance(inst: dict) -> str:
    if not isinstance(inst, dict):
        return ""
    owner = inst.get("owner") or inst.get("ownerJid") or inst.get("number") or inst.get("phone")
    if isinstance(owner, str) and owner.strip():
        return owner.strip()
    inner = inst.get("instance")
    if isinstance(inner, dict):
        owner2 = inner.get("owner") or inner.get("ownerJid") or inner.get("number") or inner.get("phone")
        if isinstance(owner2, str) and owner2.strip():
            return owner2.strip()
    return ""

def ensure_instance(instance_name: str) -> bool:
    try:
        inst = _find_instance(instance_name)
        if inst:
            return True

        payload = {
            "instanceName": instance_name,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        }

        r = requests.post(
            f"{EVOLUTION_API_URL}/instance/create",
            json=payload,
            headers=get_headers(),
            timeout=TIMEOUT_MED
        )

        if r.status_code in (200, 201):
            return True

        body = r.text or ""
        if r.status_code == 403 and ("already" in body.lower() or "exists" in body.lower()):
            return True

        return False
    except Exception:
        return False

def _sync_clinic_phone_from_instance(clinic_id: int, instance_name: str) -> dict:
    try:
        inst = _find_instance(instance_name)
        if not inst:
            return {"ok": False, "reason": "instance_not_found"}

        owner_raw = _extract_owner_from_instance(inst)
        owner_phone = _normalize_phone_from_jid(owner_raw)

        if not owner_phone:
            return {"ok": False, "reason": "owner_not_found"}

        clinic = Clinic.query.get(clinic_id)
        if not clinic:
            return {"ok": False, "reason": "clinic_not_found"}

        clinic.whatsapp_number = owner_phone
        db.session.commit()
        return {"ok": True, "owner_phone": owner_phone}
    except Exception as e:
        db.session.rollback()
        return {"ok": False, "reason": str(e)}

@bp.route('/whatsapp/qr', methods=['GET'])
@jwt_required()
def get_qr():
    clinic_id = _get_clinic_id_from_jwt()
    instance_name = get_unique_instance_name(clinic_id)

    if not ensure_instance(instance_name):
        return jsonify({"status": "error", "message": "Falha ao garantir instância"}), 500

    try:
        state = "close"
        r_state = requests.get(
            f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}",
            headers=get_headers(),
            timeout=TIMEOUT_SHORT
        )

        if r_state.status_code == 200:
            js = _safe_json(r_state) or {}
            instance_obj = js.get("instance") if isinstance(js, dict) else {}
            state = instance_obj.get("state", "close") if isinstance(instance_obj, dict) else js.get("state", "close")

        if state == 'open':
            sync = _sync_clinic_phone_from_instance(clinic_id, instance_name)
            return jsonify({"status": "connected", "synced_phone": sync.get("owner_phone")}), 200

        r_connect = requests.get(
            f"{EVOLUTION_API_URL}/instance/connect/{instance_name}",
            headers=get_headers(),
            timeout=TIMEOUT_MED
        )

        if r_connect.status_code == 200:
            js = _safe_json(r_connect) or {}
            qr_code = js.get('base64') or js.get("qrcode") or js.get("qr")
            if qr_code:
                return jsonify({"status": "disconnected", "qr_base64": qr_code}), 200

        return jsonify({"status": "disconnected", "message": "Aguardando geração do QR..."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route('/whatsapp/send', methods=['POST'])
@jwt_required()
def send_message():
    clinic_id = _get_clinic_id_from_jwt()
    instance_name = get_unique_instance_name(clinic_id)
    body = request.get_json(silent=True) or {}
    to = _digits_only(body.get("to", ""))
    message = (body.get("message", "") or "").strip()

    if not to or not message:
        return jsonify({"ok": False, "message": "Dados incompletos"}), 400

    try:
        send_url = f"{EVOLUTION_API_URL}/message/sendText/{instance_name}"
        payload = {"number": to, "text": message, "delay": 1000}
        r = requests.post(send_url, json=payload, headers=get_headers(), timeout=TIMEOUT_LONG)
        
        log = MessageLog(
            clinic_id=clinic_id,
            direction="out",
            body=message,
            status="sent" if r.status_code in (200, 201) else "failed"
        )
        db.session.add(log)
        db.session.commit()

        if r.status_code in (200, 201):
            return jsonify({"ok": True}), 200
        return jsonify({"ok": False, "error": r.text}), 400
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)}), 500
