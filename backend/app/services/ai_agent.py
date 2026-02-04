import os
import json
import logging
from datetime import datetime
from openai import OpenAI

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_DEFAULT = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """
Você é uma recepcionista de clínica odontológica no WhatsApp.
Objetivo: ajudar o paciente de forma natural e EFETIVAR ações reais chamando ferramentas quando necessário.

Regras:
- Seja curta, humana, simpática.
- Se faltar dado para agendar (data/hora/procedimento), pergunte.
- Se o usuário pedir para remarcar/cancelar, você deve usar as ferramentas.
- Confirme sempre data e hora no formato dd/mm às HH:MM.
- Nunca invente agendamentos. Só confirme após receber resultado da ferramenta.
- Use fuso America/Sao_Paulo (Brasil). Se houver ambiguidade (ex: "quinta"), pergunte confirmação.
"""

def _tool_create_appointment(clinic_id: int, phone: str, name: str, date: str, time: str, title: str, description: str):
    """
    Você vai implementar isso chamando sua lógica atual:
    - criar Appointment (start/end)
    - associar Lead/Patient
    - mover CRMCard para etapa "Agendado"
    Retorne dict com: ok, appointment_id, start_iso, human_confirm, lead_moved(bool)
    """
    from app.routes.marketing.chatbot_logic import create_real_appointment  # adapte se preferir
    data = {"date": date, "time": time, "title": title, "description": description}
    ok = create_real_appointment(clinic_id, phone, data, name)
    return {
        "ok": bool(ok),
        "human_confirm": f"{date} {time}",
    }

def _tool_reschedule_appointment(clinic_id: int, phone: str, appointment_id: int, new_date: str, new_time: str):
    """
    Implemente:
    - buscar appointment por id + clinic_id
    - atualizar start/end no fuso correto
    - registrar histórico
    """
    # placeholder
    return {"ok": False, "reason": "not_implemented"}

def _tool_move_lead_stage(clinic_id: int, phone: str, stage_name: str):
    """
    Implemente:
    - achar CRMCard open pelo phone
    - achar CRMStage por nome
    - atualizar stage_id
    """
    # placeholder
    return {"ok": False, "reason": "not_implemented"}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_appointment",
            "description": "Cria um agendamento real no sistema (banco), associando lead/paciente e movendo no CRM se aplicável.",
            "parameters": {
                "type": "object",
                "properties": {
                    "clinic_id": {"type": "integer"},
                    "phone": {"type": "string"},
                    "name": {"type": "string"},
                    "date": {"type": "string", "description": "Data no formato YYYY-MM-DD"},
                    "time": {"type": "string", "description": "Hora no formato HH:MM (24h)"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["clinic_id", "phone", "name", "date", "time", "title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reschedule_appointment",
            "description": "Remarca um agendamento existente para nova data/hora.",
            "parameters": {
                "type": "object",
                "properties": {
                    "clinic_id": {"type": "integer"},
                    "phone": {"type": "string"},
                    "appointment_id": {"type": "integer"},
                    "new_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "new_time": {"type": "string", "description": "HH:MM"},
                },
                "required": ["clinic_id", "phone", "appointment_id", "new_date", "new_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "move_lead_stage",
            "description": "Move o card do lead no CRM para uma etapa por nome (ex: Agendado, Contactado, Perdido).",
            "parameters": {
                "type": "object",
                "properties": {
                    "clinic_id": {"type": "integer"},
                    "phone": {"type": "string"},
                    "stage_name": {"type": "string"},
                },
                "required": ["clinic_id", "phone", "stage_name"]
            }
        }
    },
]

def handle_message(clinic_id: int, phone: str, push_name: str, user_text: str, conversation_snippet: str = "") -> str:
    """
    Retorna a resposta final (texto) para enviar no WhatsApp.
    conversation_snippet: opcional (últimas 6-10 msgs), pra dar contexto com baixo custo.
    """

    input_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    if conversation_snippet:
        input_messages.append({"role": "system", "content": f"Histórico recente:\n{conversation_snippet}"})

    input_messages.append({
        "role": "user",
        "content": f"Paciente: {push_name} ({phone})\nMensagem: {user_text}\n"
                  f"clinic_id={clinic_id}\n"
                  f"Responda em pt-BR."
    })

    # 1) primeira chamada: o modelo pode pedir tools
    resp = client.responses.create(
        model=MODEL_DEFAULT,
        input=input_messages,
        tools=TOOLS,
        tool_choice="auto",
        # importante pra reduzir custo e evitar guardar conversa no provedor, se você quiser:
        store=False,
        max_output_tokens=350
    )

    # Verifica se houve tool calls
    tool_calls = []
    for item in resp.output:
        if item.type == "tool_call":
            tool_calls.append(item)

    # Se não teve tool call, pega o texto e retorna
    if not tool_calls:
        return _extract_text(resp)

    # 2) executa as tools e devolve resultados ao modelo
    tool_outputs = []
    for call in tool_calls:
        name = call.name
        args = call.arguments or {}
        try:
            if name == "create_appointment":
                result = _tool_create_appointment(**args)
            elif name == "reschedule_appointment":
                result = _tool_reschedule_appointment(**args)
            elif name == "move_lead_stage":
                result = _tool_move_lead_stage(**args)
            else:
                result = {"ok": False, "reason": "unknown_tool"}

        except Exception as e:
            logger.exception("Tool execution failed")
            result = {"ok": False, "reason": str(e)}

        tool_outputs.append({
            "type": "tool_output",
            "tool_call_id": call.id,
            "output": json.dumps(result, ensure_ascii=False)
        })

    # 3) segunda chamada: agora ele responde confirmando com base no resultado real
    resp2 = client.responses.create(
        model=MODEL_DEFAULT,
        input=input_messages,
        tools=TOOLS,
        tool_choice="none",
        store=False,
        max_output_tokens=250,
        previous_response_id=resp.id,
        output=tool_outputs
    )

    return _extract_text(resp2)

def _extract_text(resp) -> str:
    chunks = []
    for item in resp.output:
        if item.type == "output_text":
            chunks.append(item.text)
    text = "\n".join(chunks).strip()
    return text or "Certo! Pode me dizer a data e horário que você prefere?"
