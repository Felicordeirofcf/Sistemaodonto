import logging
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

evolution_bp = Blueprint("evolution_bp", __name__)

@evolution_bp.get("/evolution/health")
def evolution_health():
    return jsonify({"ok": True}), 200


@evolution_bp.route("/evolution/functions", methods=["GET", "POST"])
def evolution_functions():
    """
    O painel do Evolution pode fazer GET para testar.
    E o bot pode fazer POST quando realmente chamar tools.
    """
    payload = request.get_json(silent=True) or {}
    logger.info("EVOLUTION FUNCTIONS CALL method=%s payload=%s", request.method, payload)
    return jsonify({"ok": True, "message": "functions endpoint alive"}), 200
