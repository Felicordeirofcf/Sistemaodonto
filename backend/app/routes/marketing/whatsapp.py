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

# timeouts (evita travar request)
TIMEOUT_SHORT = 10
TIMEOUT_MED = 20
TIMEOUT_LONG = 30


# =========================================================
# Helpers
# =========================================================
def get_headers():
    return {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }

def _get_clinic_id_from_jwt() -> int:
    identity = get_jwt_identity()
    if isinstance(identity, dict):
        cid = identity.get("clinic_id") or identity.get("id")
        try:
            return int(cid)
        except Exception:
            return 1
    # se vier string ou outro formato
    return 1

def get_unique_instance_name() -> str:
    # Isolamento SaaS por clinic_id (MUITO importante)
    clinic_id = _get_clinic_id_from_jwt()
    return f"clinica_v3_{clinic_id}"

def _digits_only(s: str) -> str:
    return "".join([c for c in (s or "") if c.isdigit()])

def _normalize_phone_from_jid(jid: str) -> str:
    # "5511999999999@s.whatsapp.net" -> "5511999999999"
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


# =========================================================
# Evolution API helpers
# =========================================================
def _fetch_instances():
    """
    Tenta obter lista de instâncias da Evolution.
    Alguns retornam list diretamente, outros retornam {"instances": [...]}
    """
    url = f"{EVOLUTION_API_URL}/instance/fetchInstances"
    r = requests.get(url, headers=get_headers(), timeout=TIMEOUT_SHORT)
    data = _safe_json(r)

    if r.status_code != 200 or data is None:
        return []

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # variações comuns
        for key in ("instances", "data", "response"):
            if isinstance(data.get(key), list):
                return data.get(key)

    return []

def _find_instance(instance_name: str):
    instances = _fetch_instances()
    for inst in instances:
        if not isinstance(inst, dict):
            continue
        # variações comuns de nome
        name = inst.get("instanceName") or inst.get("name") or inst.get("instance") or ""
        if name == instance_name:
            return inst
    return None

def _extract_owner_from_instance(inst: dict) -> str:
    """
    Tenta pegar o número/owner da instância (depende da versão da Evolution).
    Campos comuns:
      - inst["owner"]
      - inst["instance"]["owner"]
      - inst["instance"]["ownerJid"]
      - inst["number"]
      - inst["phone"]
    """
    if not isinstance(inst, dict):
        return ""

    # 1) direto
    owner = inst.get("owner") or inst.get("ownerJid") or inst.get("number") or inst.get("phone")
    if isinstance(owner, str) and owner.strip():
        return owner.strip()

    # 2) aninhado
    inner = inst.get("instance")
    if isinstance(inner, dict):
        owner2 = inner.get("owner") or inner.get("ownerJid") or inner.get("number") or inner.get("phone")
        if isinstance(owner2, str) and owner2.strip():
            return owner2.strip()

    return ""

def ensure_instance(instance_name: str) -> bool:
    """
    Garante que a instância exista.
    Se já existir, não tenta recriar.
    Se tentar criar e receber 403 'already in use', trata como OK.
    """
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

        # ✅ importante: se já existir, treat as OK (seu log mostra 403)
        body = r.text or ""
        if r.status_code == 403 and "already" in body.lower() and "use" in body.lower():
            logger.warning(f"⚠️ ensure_instance: instância já existe ({instance_name}). Continuando...")
            return True

        logger.warning(f"⚠️ ensure_instance create status={r.status_code} body={body}")
        return False

    except Exception as e:
        logger.exception(f"Erro ao garantir instância: {e}")
        return False


def _sync_clinic_phone_from_instance(clinic_id: int, instance_name: str) -> dict:
    """
    Quando a instância estiver conectada, pega owner/phone e salva no Clinic.whatsapp_number.
    Retorna dict com status para debug.
    """
    try:
        inst = _find_instance(instance_name)
        if not inst:
            return {"ok": False, "reason": "instance_not_found_in_fetch"}

        owner_raw = _extract_owner_from_instance(inst)
        owner_phone = _normalize_phone_from_jid(owner_raw)

        if not owner_phone:
            return {"ok": False, "reason": "owner_not_found", "owner_raw": owner_raw}

        clinic = Clinic.query.get(clinic_id)
        if not clinic:
            return {"ok": False, "reason": "clinic_not_found"}

        clinic.whatsapp_number = owner_phone

        # opcional: guardar o nome da instância no Clinic se existir campo
        if hasattr(clinic, "whatsapp_instance"):
            clinic.whatsapp_instance = instance_name

        db.session.commit()

        return {"ok": True, "owner_phone": owner_phone, "instance_name": instance_name}

    except Exception as e:
        db.session.rollback()
        logger.exception(f"Erro ao sync phone da clínica: {e}")
        return {"ok": False, "reason": "exception", "error": str(e)}


# =========================================================
# 1) ROTA PARA SALVAR O NÚMERO MANUALMENTE (fallback)
# =========================================================
@bp.route('/whatsapp/settings', methods=['POST'])
@jwt_required()
def save_settings():
    clinic_id = _get_clinic_id_from_jwt()
    data = request.get_json(silent=True) or {}

    raw_phone = data.get('whatsapp_number', '')
    clean_phone = _digits_only(raw_phone)

    if not clean_phone:
        return jsonify({"ok": False, "message": "Número inválido"}), 400

    clinic = Clinic.query.get(clinic_id)
    if clinic:
        clinic.whatsapp_number = clean_phone
        db.session.commit()
        return jsonify({"ok": True, "message": "Número atualizado!", "number": clean_phone}), 200

    return jsonify({"ok": False, "message": "Clínica não encontrada"}), 404


# =========================================================
# 2) ROTA DE QR CODE E CONEXÃO (COM AUTO-SYNC DO NÚMERO)
# =========================================================
@bp.route('/whatsapp/qr', methods=['GET'])
@jwt_required()
def get_qr():
    clinic_id = _get_clinic_id_from_jwt()
    instance_name = get_unique_instance_name()

    if not ensure_instance(instance_name):
        return jsonify({"status": "error", "message": "Falha ao garantir instância"}), 500

    try:
        # 1) Busca estado da conexão
        state = "close"
        r_state = requests.get(
            f"{EVOLUTION_API_URL}/instance/connectionState/{instance_name}",
            headers=get_headers(),
            timeout=TIMEOUT_SHORT
        )

        if r_state.status_code == 200:
            js = _safe_json(r_state) or {}
            # variações de retorno
            instance_obj = js.get("instance") if isinstance(js, dict) else {}
            if isinstance(instance_obj, dict):
                state = instance_obj.get("state", "close")
            else:
                # fallback (alguns retornam direto)
                state = js.get("state", "close") if isinstance(js, dict) else "close"

        # 2) Se conectado: ✅ sincroniza telefone automaticamente
        if state == 'open':
            sync = _sync_clinic_phone_from_instance(clinic_id, instance_name)
            if not sync.get("ok"):
                logger.warning(f"⚠️ Conectado, mas sync phone falhou: {sync}")
                # mesmo assim, retorna conectado (para UI), mas com aviso
                return jsonify({"status": "connected", "warning": "connected_but_no_phone_synced"}), 200

            return jsonify({"status": "connected", "synced_phone": sync.get("owner_phone")}), 200

        # 3) Se não conectado: gera QR
        r_connect = requests.get(
            f"{EVOLUTION_API_URL}/instance/connect/{instance_name}",
            headers=get_headers(),
            timeout=TIMEOUT_MED
        )

        if r_connect.status_code == 200:
            js = _safe_json(r_connect) or {}
            qr_code = js.get('base64') or js.get("qrcode") or js.get("qr")  # variações
            if qr_code:
                return jsonify({"status": "disconnected", "qr_base64": qr_code}), 200

        return jsonify({"status": "disconnected", "message": "Aguardando geração do QR..."}), 200

    except Exception as e:
        logger.exception(f"Erro ao obter QR: {e}")
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
    to = _digits_only(body.get("to", ""))
    message = (body.get("message", "") or "").strip()

    if not to or not message:
        return jsonify({"ok": False, "message": "Dados incompletos"}), 400

    try:
        send_url = f"{EVOLUTION_API_URL}/message/sendText/{instance_name}"
        payload = {"number": to, "text": message, "delay": 1000}

        r = requests.post(send_url, json=payload, headers=get_headers(), timeout=TIMEOUT_LONG)

        # Log da mensagem no banco
        try:
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

        return jsonify({"ok": False, "error": r.text, "status_code": r.status_code}), 400

    except Exception as e:
        logger.exception(f"Erro ao enviar mensagem: {e}")
        return jsonify({"ok": False, "message": "Erro de conexão"}), 500


@bp.route('/whatsapp/health', methods=['GET'])
def health():
    return jsonify({"status": "online"}), 200
