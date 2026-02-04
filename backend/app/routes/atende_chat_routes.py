from flask import Blueprint, request, jsonify

from app.services.ai_client import chat_reply, vision_reply, get_openai_client

atende_chat_bp = Blueprint("atende_chat", __name__)

# Prompt para conversa normal
TEXT_PROMPT = (
    "Você é a Ana, Consultora Estética da OdontoSys. "
    "Responda em pt-BR, seja simpática, objetiva e profissional. "
    "Nunca invente diagnósticos, preços ou promessas médicas."
)

# Prompt para análise de imagem (visão)
VISION_PROMPT = (
    "Você é uma consultora de clínica odontológica. "
    "Ao receber uma foto de sorriso/dentes, faça uma análise geral (sem diagnóstico), "
    "explique possibilidades de tratamento (ex: clareamento, facetas, alinhadores), "
    "faça 2-4 perguntas rápidas para coletar informações e sugerir agendamento."
)


@atende_chat_bp.get("/ai/health")
def ai_health():
    """Diagnóstico de IA.

    Retorna 200 se OPENAI_API_KEY estiver configurada.
    Retorna 500 com mensagem clara se faltar a chave.
    """
    import os

    try:
        get_openai_client()
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        return jsonify({"ok": True, "provider": "openai", "model": model}), 200
    except Exception as e:
        return jsonify({"ok": False, "provider": "openai", "error": str(e)}), 500


@atende_chat_bp.route("/chat/message", methods=["POST"])
def chat_message():
    """Rota de chat (site).

    - Sem imagem: usa chat_reply.
    - Com imagem: usa vision_reply (apenas análise; não gera imagem).
    """
    image_file = request.files.get("image")
    text_message = request.form.get("message", "")

    if not image_file:
        try:
            out = chat_reply(TEXT_PROMPT, text_message)
            return jsonify({"response": out}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    try:
        img_bytes = image_file.read()
        mime = image_file.mimetype or "image/jpeg"
        out = vision_reply(VISION_PROMPT, text_message or "Analise a imagem.", img_bytes, mime)
        # mantém compatibilidade do front (campo image existia antes)
        return jsonify({"response": out, "image": None}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
