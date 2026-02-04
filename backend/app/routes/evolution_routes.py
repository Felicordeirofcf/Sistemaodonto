import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

evolution_bp = Blueprint("evolution_bp", __name__)

@evolution_bp.get("/evolution/health")
def evolution_health():
    return jsonify({"ok": True}), 200

@evolution_bp.post("/evolution/functions")
def evolution_functions():
    payload = request.get_json(silent=True) or {}
    logger.info("EVOLUTION FUNCTIONS CALL payload=%s", payload)
    return jsonify({"ok": True, "message": "functions endpoint alive"}), 200
