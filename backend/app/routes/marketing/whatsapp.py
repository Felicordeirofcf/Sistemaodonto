import os
import requests
import logging
import json
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db, WhatsAppContact, MessageLog, Clinic, WhatsAppConnection

bp = Blueprint("marketing_whatsapp", __name__)
logger = logging.getLogger(__name__)

# --- CONFIGURAÇÕES ---
EVOLUTION_API_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "minha-senha-secreta")

# Se quiser ter um fallback global (evite hardcode em produção)
DEFAULT_CLINIC_WHATSAPP = os.getenv("DEFAULT_CLINIC_WHATSAPP", "")

startup_cooldown = {}


# =========================================================
# Helpers
# =========================================================

def get_headers():
    return {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }

def _only_digits(value: str) -> str:
    return "".join(filter(str.isdigit, value or ""))

def _get_clinic_id_from_jwt():
    identity = get_jwt_identity()
    if isinstance(identity, dict) and identity.get("clinic_id"):
        return int(identity["clinic_id"])
    return 1

def get_unique_instance_name():
    """
    Instância isolada por clínica (SaaS).
    """
    identity = get_jwt_identity()
    clinic_id = "1"
    if isinstance(identity, dict):
        clinic_id = str(identity.get("clinic_id") or identity.get("id") or "1")
    return f"clinica_v3_{clinic_id}"

def ensure_instance(instance_name: str) -> bool:
    """
    Garante que a instância exista na Evolution.
    """
    try:
        r = requests.get(
            f"{EVOLUTION_API_URL}/instance/fetchInstances",
            headers=get_headers(),
            timeout=10
        )
        if r.status_code == 200:
            instances = r.json()
            if isinstance(instances, list):
                for inst in instances:
                    if isinstance(inst, dict) and inst.get("instanceName") == instance_name:
                        return True

        # Cria instância se não existir
        payload = {
            "instanceName": instance_name,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS"
        }
        r_create = requests.post(
            f"{EVOLUTION_API_URL}/instance/create",
            json=payload,
            headers=get_headers(),
            timeout=20
        )

        # Mesmo se não retornar 200/201, pode ter criado; então consideramos ok se não explodiu
        if r_create.status_code in (200, 201):
            return True

        logger.warning(f"⚠️ ensure_instance create status={r_create.status_code} body={r_create.text}")
        return True

    except Exception as e:
        logger.exception(f"Erro ao garantir instância: {e}")
        return False


def sync_connected_phone_to_clinic(clinic_id: int, instance_name: str):
    """
    Quando a instância estiver CONNECTED, tenta descobrir o número conectado e salvar
    em Clinic.whatsapp_number.

    Retorna: (ok: bool, phone: str, debug: dict)
    """
    try:
        r = requests.get(
            f"{EVOLUTION_API_URL}/instance/fetchInstances",
            headers=get_headers(),
            timeout=10
        )

        if r.status_code != 200:
            return False, "", {
                "error": "fetchInstances failed",
                "status": r.status_code,
                "text": r.text
            }

        instances = r.json()
        if not isinstance(instances, list):
            return False, "", {"error": "fetchInstances not list", "json": instances}

        target = None
        for inst in instances:
            if isinstance(inst, dict) and inst.get("instanceName") == instance_name:
                target = inst
                break

        if not target:
            return False, "", {"error": "instance not found", "instanceName": instance_name}

        # tenta encontrar o número em diferentes campos possíveis
        # (depende da versão/retorno da Evolution)
        candidates = [
            target.get("owner"),
            target.get("ownerJid"),
            target.get("number"),
            target.get("phone"),
        ]

        # alguns retornam nested dict
        me = target.get("me")
        if isinstance(me, dict):
            candidates.append(me.get("id"))
            candidates.append(me.get("jid"))
            candidates.append(me.get("number"))

        profile = target.get("profile")
        if isinstance(profile, dict):
            candidates.append(profile.get("id"))
            candidates.append(profile.get("jid"))

        phone = ""
        for c in candidates:
            if isinstance(c, str) and c.strip():
                cleaned = c.strip().split("@")[0].split(":")[0]
                phone = _only_digits(cleaned)
                if phone:
                    break

        if not phone and DEFAULT_CLINIC_WHATSAPP:
            phone = _only_digits(DEFAULT_CLINIC_WHATSAPP)

        if not phone:
            return False, "", {"error": "phone not found", "target": target}

        clinic = Clinic.query.get(clinic_id)
        if not clinic:
            return False, "", {"error": "clinic not found", "clinic_id": clinic_id}

        clinic.whatsapp_number = phone

        # Se você tiver esse campo no model Clinic, salva. Se não tiver, ignora.
        if hasattr(clinic, "whatsapp_instance"):
            setattr(clinic, "whatsapp_instance", instance_name)

        db.session.commit()
        return True, phone, {"source": "fetchInstances", "instance": instance_name}

    except Exception as e:
        db.session.rollback()
        logger.exception(f"sync_connected_phone_to_clinic error: {e}")
        return False, "", {"error": str(e)}


# =========================================================
# 1) ROTA PARA SALVAR O NÚMERO FIXO (MANUAL)
# =========================================================
@bp.route('/whatsapp/settings', methods=['POST'])
@jwt_required()
def save_settings():
    clinic_id = _get_clinic_id_from_jwt()
    data = request.get_json(silent=True) or {}

    raw_phone = data.get('whatsapp_number', '')
    clean_phone = _only_digits(raw_phone)

    if not clean_phone:
        return jsonify({"ok": False, "message": "Número inválido"}), 400

    clinic = Clinic.query.get(clinic_id)
    if not clinic:
        return jsonify({"ok": False, "message": "Clínica não encontrada"}), 404

    clinic.whatsapp_number = clean_phone
    db.session.commit()
    return jsonify({"ok": True, "message": "Número atualizado!", "number": clean_phone}), 200


# =========================================================
# 2) QR CODE E CONEXÃO (COM SYNC AUTOMÁTICO DO NÚMERO)
# =========================================================
@bp.route('/whatsapp/qr', methods=['GET'])
@jwt_required()
def get_qr():
    clinic_id = _get_clinic_id_from_jwt()
    instance_name = get_unique_instance_name()

    if not ensure_instance(instance_name):
        return jsonify({"status": "error", "message": "Falha ao criar/validar instância"}), 500

    try:
        # 1) Busca estado da conexão
        state = "close"
        r_state = requests.get(
            f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}",
            headers=get_headers(),
            timeout=10
        )
        if r_state.status_code == 200:
            # alguns retornos vêm em {"instance": {"state": "open"}}
            data_state = r_state.json()
            if isinstance(data_state, dict):
                state = (data_state.get('instance') or {}).get('state', 'close')

        # 2) Se conectado, tenta salvar número automaticamente na clínica
        if state == 'open':
            ok, phone, debug = sync_connected_phone_to_clinic(clinic_id, instance_name)
            if ok:
                return jsonify({"status": "connected", "phone_saved": phone, "instance": instance_name}), 200
            else:
                logger.warning(f"⚠️ Conectado, mas sync phone falhou: {debug}")
                return jsonify({
                    "status": "connected",
                    "phone_saved": None,
                    "instance": instance_name,
                    "sync_warning": debug
                }), 200

        # 3) Se desconectado, gera novo QR
        r_connect = requests.get(
            f"{EVOLUTION_API_URL}/instance/connect/{instance_name}",
            headers=get_headers(),
            timeout=20
        )
        if r_connect.status_code == 200:
            qr_code = (r_connect.json() or {}).get('base64')
            return jsonify({"status": "disconnected", "qr_base64": qr_code, "instance": instance_name}), 200

        return jsonify({"status": "disconnected", "message": "Iniciando...", "instance": instance_name}), 200

    except Exception as e:
        logger.exception(f"Erro no get_qr: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# =========================================================
# 3) ROTA DE ENVIO
# =========================================================
@bp.route('/whatsapp/send', methods=['POST'])
@jwt_required()
def send_message():
    clinic_id = _get_clinic_id_from_jwt()
    instance_name = get_unique_instance_name()

    body = request.get_json(silent=True) or {}
    to = _only_digits(body.get("to", ""))
    message = (body.get("message") or "").strip()

    if not to or not message:
        return jsonify({"ok": False, "message": "Dados incompletos (to/message)"}), 400

    try:
        send_url = f"{EVOLUTION_API_URL}/message/sendText/{instance_name}"
        payload = {"number": to, "text": message, "delay": 1000}

        r = requests.post(send_url, json=payload, headers=get_headers(), timeout=30)

        # Log da mensagem no banco
        try:
            log = MessageLog(
                clinic_id=clinic_id,
                direction="out",
                body=message,
                status="sent" if r.status_code in (200, 201) else "failed",
                created_at=datetime.utcnow() if hasattr(MessageLog, "created_at") else None
            )
            # se seu model tiver campos extras, você pode salvar também:
            if hasattr(log, "to_phone"):
                setattr(log, "to_phone", to)
            if hasattr(log, "instance_name"):
                setattr(log, "instance_name", instance_name)

            db.session.add(log)
            db.session.commit()
        except Exception:
            db.session.rollback()

        if r.status_code in (200, 201):
            return jsonify({"ok": True}), 200

        return jsonify({"ok": False, "error": r.text, "status_code": r.status_code}), 400

    except Exception as e:
        logger.exception(f"Erro ao enviar mensagem: {e}")
        return jsonify({"ok": False, "message": "Erro de conexão"}), 500


@bp.route('/whatsapp/health', methods=['GET'])
def health():
    return jsonify({"status": "online"}), 200
