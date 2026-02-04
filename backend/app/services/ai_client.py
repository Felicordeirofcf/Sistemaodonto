import base64
import os
from typing import Any, Dict, List, Optional, Union

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


_DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_DEFAULT_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.4"))


def get_openai_client() -> "OpenAI":
    """Retorna o client OpenAI (lazy).

    Requisitos:
      - OPENAI_API_KEY no ambiente
      - pacote openai instalado
    """
    if OpenAI is None:
        raise RuntimeError("Dependência 'openai' não encontrada. Garanta 'openai' no requirements.")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não está configurada no ambiente.")

    return OpenAI(api_key=api_key)


def _extract_overrides(history: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]]):
    """Permite overrides sem quebrar a assinatura pública.

    Aceita:
      - history: list[{'role','content'}]
      - history: {'messages': [...], 'model': '...', 'temperature': 0.4, 'max_tokens': 300}
    """
    if isinstance(history, dict):
        msgs = history.get("messages")
        if not isinstance(msgs, list):
            msgs = []
        model = (history.get("model") or _DEFAULT_MODEL)
        temperature = float(
            history.get("temperature") if history.get("temperature") is not None else _DEFAULT_TEMPERATURE
        )
        max_tokens = int(history.get("max_tokens") if history.get("max_tokens") is not None else 350)
        return msgs, model, temperature, max_tokens

    if isinstance(history, list):
        return history, _DEFAULT_MODEL, _DEFAULT_TEMPERATURE, 350

    return [], _DEFAULT_MODEL, _DEFAULT_TEMPERATURE, 350


def chat_reply(system_prompt: str, user_text: str, history: Optional[Union[List[Dict[str, Any]], Dict[str, Any]]] = None) -> str:
    """Resposta de chat (texto) via OpenAI."""
    client = get_openai_client()
    hist, model, temperature, max_tokens = _extract_overrides(history)

    messages: List[Dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    for item in hist:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role in ("user", "assistant", "system") and isinstance(content, str) and content.strip():
            messages.append({"role": role, "content": content[:6000]})

    messages.append({"role": "user", "content": (user_text or "").strip()[:8000]})

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()


def vision_reply(system_prompt: str, user_text: str, image_bytes: bytes, image_mime: str) -> str:
    """Resposta com visão (texto + imagem) via OpenAI.

    Observação: usa o modelo/temperatura padrão do ambiente (OPENAI_MODEL/OPENAI_TEMPERATURE).
    """
    client = get_openai_client()
    _, model, temperature, max_tokens = _extract_overrides(None)

    if not image_bytes:
        raise ValueError("image_bytes vazio")

    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{image_mime};base64,{b64}"

    messages: List[Dict[str, Any]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append(
        {
            "role": "user",
            "content": [
                {"type": "text", "text": (user_text or "").strip()[:4000]},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }
    )

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()
