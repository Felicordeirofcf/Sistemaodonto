from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db, Clinic

bp = Blueprint("marketing_ai", __name__)


def _get_clinic_id_from_jwt() -> int:
    identity = get_jwt_identity()
    if isinstance(identity, dict) and identity.get("clinic_id"):
        try:
            return int(identity["clinic_id"])
        except Exception:
            return 1
    return 1


@bp.route("/ai/settings", methods=["GET"])
@jwt_required()
def get_ai_settings():
    clinic_id = _get_clinic_id_from_jwt()
    clinic = Clinic.query.get_or_404(clinic_id)

    return jsonify({
        "ai_enabled": bool(getattr(clinic, "ai_enabled", True)),
        "ai_model": getattr(clinic, "ai_model", None) or "gpt-4o-mini",
        "ai_temperature": float(getattr(clinic, "ai_temperature", 0.4) or 0.4),
        "ai_system_prompt": getattr(clinic, "ai_system_prompt", None),
        "ai_procedures": getattr(clinic, "ai_procedures", None),
        "ai_booking_policy": getattr(clinic, "ai_booking_policy", None),
    }), 200


@bp.route("/ai/settings", methods=["PUT"])
@jwt_required()
def update_ai_settings():
    clinic_id = _get_clinic_id_from_jwt()
    clinic = Clinic.query.get_or_404(clinic_id)
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"error": "JSON inválido"}), 400

    if "ai_enabled" in data:
        clinic.ai_enabled = bool(data.get("ai_enabled"))

    if "ai_model" in data and isinstance(data.get("ai_model"), str):
        clinic.ai_model = data.get("ai_model").strip() or "gpt-4o-mini"

    if "ai_temperature" in data:
        try:
            t = float(data.get("ai_temperature"))
            clinic.ai_temperature = max(0.0, min(1.2, t))
        except Exception:
            pass

    if "ai_system_prompt" in data:
        clinic.ai_system_prompt = (data.get("ai_system_prompt") or "").strip() or None

    if "ai_procedures" in data:
        # Deve ser JSON (objeto) com descrições/duração/etc.
        proc = data.get("ai_procedures")
        if proc is not None and not isinstance(proc, dict):
            return jsonify({"error": "ai_procedures deve ser um objeto JSON"}), 400
        clinic.ai_procedures = proc

    if "ai_booking_policy" in data:
        clinic.ai_booking_policy = (data.get("ai_booking_policy") or "").strip() or None

    db.session.commit()
    return jsonify({"success": True}), 200
