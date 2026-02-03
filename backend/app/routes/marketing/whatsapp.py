import os
import requests
import logging
import json
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db, Clinic, MessageLog

bp = Blueprint("marketing_whatsapp", __name__)
logger = logging.getLogger(__name__)

EVOLUTION_API_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "minha-senha-secreta")


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def get_headers():
    return {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}

def _safe_json(resp):
    try:
        return resp.json()
    except Exception:
        return None

def _get_clinic_id_from_jwt():
    identity = get_jwt_identity()
    if isinstance(identity, dict):
        return int(identity.get("clinic_id") or identity.get("id") or 1)
    return 1

def get_unique_instance_name():
    clinic_id = _get_clinic_id_from_jwt()
    return f"clinica_v3_{clinic_id}"

def _extract_instances_list(payload):
    """
    Evolution pode retornar:
      - lista direta: [ {..}, {..} ]
      - dict: { "instances": [..] }
      - dict: { "data": [..] }
    """
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for k in ("instances", "data", "response"):
            if isinstance(payload.get(k), list):
                return payload.get(k)
    return []

def _get_instance_name_from_item(item: dict) -> str:
    """
    Itens podem ter chaves diferentes:
      instanceName, name, instance, id etc.
    """
    if not isinstance(item, dict):
        return ""
    for k in ("instanceName", "name", "instance", "instance_name"):
        v = item.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


# -------------------------------------------------------------------
# 1) SETTINGS (NÚMERO ÂNCORA)
# -------------------------------------------------------------------

@bp.route('/whatsapp/settings', methods=['POST'])
@jwt_required()
def save_settings():
    clinic_id = _get_clinic_id_from_jwt()
    data = request.get_json(silent=True) or {}

    raw_phone = data.get('whatsapp_number', '')
    clean_phone = "".join(filter(str.isdigit, raw_phone))

    if not clean_phone:
        return jsonify({"ok": False, "message": "Número inválido"}), 400

    clinic = Clinic.query.get(clinic_id)
    if not clinic:
        return jsonify({"ok": False, "message": "Clínica não encontrada"}), 404

    clinic.whatsapp_number = clean_phone
    db.session.commit()
    return jsonify({"ok": True, "message": "Número atualizado!", "number": clean_phone}), 200


# -------------------------------------------------------------------
# 2) INSTÂNCIA (EVOLUTION)
# -------------------------------------------------------------------

def ensure_instance(instance_name: str) -> bool:
    """
    Garante que a instância exista.
    - Detecta instância existente (vários formatos de retorno)
    - Se create retornar 403 "already in use", considera OK.
    """
    try:
        # 1) listar instâncias
        r = requests.get(
            f"{EVOLUTION_API_URL}/instance/fetchInstances",
            headers=get_headers(),
            timeout=15
        )

        if r.status_code == 200:
            payload = _safe_json(r)
            instances = _extract_instances_list(payload)

            for inst in instances:
                name = _get_instance_name_from_item(inst)
                if name == instance_name:
                    return True

        # 2) criar instância
        create_payload = {
            "instanceName": instance_name,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        }

        r_create = requests.post(
            f"{EVOLUTION_API_URL}/instance/create",
            json=create_payload,
            headers=get_headers(),
            timeout=20
        )

        if r_create.status_code in (200, 201):
            return True

        # ✅ Fix: se já existe, Evolution pode responder 403 "already in use"
        body = r_create.text or ""
        if r_create.status_code == 403 and "already in use" in body.lower():
            logger.warning(f"⚠️ ensure_instance: name already in use -> assumindo existente: {instance_name}")
            return True

        logger.warning(f"⚠️ ensure_instance create status={r_create.status_code} body={body}")
        return False

    except Exception as e:
        logger.exception(f"Erro ao garantir instância {instance_name}: {e}")
        return False


def get_connection_state(instance_name: str) -> str:
    """
    Retorna state 'open'/'close'/etc.
    """
    try:
        r = requests.get(
            f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}",
            headers=get_headers(),
            timeout=15
        )
        if r.status_code == 200:
            js = _safe_json(r) or {}
            # formatos comuns:
            # { "instance": { "state": "open" } }
            state = (js.get("instance") or {}).get("state")
            if isinstance(state, str):
                return state
        else:
            logger.warning(f"⚠️ connectionState status={r.status_code} body={r.text}")
    except Exception as e:
        logger.warning(f"⚠️ connectionState erro: {e}")

    return "close"


# -------------------------------------------------------------------
# 3) QR CODE / CONEXÃO
# -------------------------------------------------------------------

@bp.route('/whatsapp/qr', methods=['GET'])
@jwt_required()
def get_qr():
    instance_name = get_unique_instance_name()

    # 1) garante instância
    ok = ensure_instance(instance_name)
    if not ok:
        return jsonify({"status": "error", "message": "Falha ao garantir instância do WhatsApp"}), 500

    # 2) verifica estado
    state = get_connection_state(instance_name)
    if state == "open":
        return jsonify({"status": "connected"}), 200

    # 3) pede QR
    try:
        r_connect = requests.get(
            f"{EVOLUTION_API_URL}/instance/connect/{instance_name}",
            headers=get_headers(),
            timeout=25
        )

        if r_connect.status_code == 200:
            js = _safe_json(r_connect) or {}
            qr_base64 = js.get("base64")
            if qr_base64:
                return jsonify({"status": "disconnected", "qr_base64": qr_base64}), 200

            # algumas versões retornam em outros campos
            qr_base64 = js.get("qrcode") or js.get("qr")
            if qr_base64:
                return jsonify({"status": "disconnected", "qr_base64": qr_base64}), 200

            return jsonify({"status": "disconnected", "message": "QR não retornado pela Evolution"}), 200

        # se retornou 404, é sinal de instância realmente não encontrada
        logger.warning(f"⚠️ connect status={r_connect.status_code} body={r_connect.text}")
        return jsonify({"status": "disconnected", "message": "Iniciando..." }), 200

    except Exception as e:
        logger.exception(f"Erro ao buscar QR: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# -------------------------------------------------------------------
# 4) ENVIO DE MSG (EVOLUTION)
# -------------------------------------------------------------------

@bp.route('/whatsapp/send', methods=['POST'])
@jwt_required()
def send_message():
    instance_name = get_unique_instance_name()
    body = request.get_json(silent=True) or {}

    to = "".join(filter(str.isdigit, body.get("to", "")))
    message = (body.get("message") or "").strip()

    if not to or not message:
        return jsonify({"ok": False, "message": "Dados incompletos"}), 400

    # garante que instância exista
    if not ensure_instance(instance_name):
        return jsonify({"ok": False, "message": "Instância WhatsApp indisponível"}), 500

    try:
        send_url = f"{EVOLUTION_API_URL}/message/sendText/{instance_name}"
        payload = {"number": to, "text": message, "delay": 1000}

        r = requests.post(send_url, json=payload, headers=get_headers(), timeout=30)

        # Log no banco
        try:
            clinic_id = _get_clinic_id_from_jwt()
            log = MessageLog(
                clinic_id=clinic_id,
                direction="out",
                body=message,
                status="sent" if r.status_code in (200, 201) else "failed"
            )
            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()

        if r.status_code in (200, 201):
            return jsonify({"ok": True}), 200

        return jsonify({"ok": False, "error": r.text, "status": r.status_code}), 400

    except Exception as e:
        logger.exception(f"Erro ao enviar mensagem: {e}")
        return jsonify({"ok": False, "message": "Erro de conexão"}), 500


@bp.route('/whatsapp/health', methods=['GET'])
def health():
    return jsonify({"status": "online"}), 200
