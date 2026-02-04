import logging
import json
import uuid
import re
import os
from datetime import datetime, timedelta

# ✅ timezone robusto (Python 3.9+)
from zoneinfo import ZoneInfo

from app.models import db, ChatSession, Appointment, Patient, Lead, Clinic, CRMCard, CRMStage
from .webhook import _send_whatsapp_reply

# ✅ Serviço central de IA (OpenAI)
from app.services.ai_client import chat_reply

logger = logging.getLogger(__name__)

TZ_SP = ZoneInfo("America/Sao_Paulo")

# ------------------------------------------------------------------------------
# Config IA (padrões)
# ------------------------------------------------------------------------------
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.4"))

DEFAULT_SYSTEM_PROMPT = os.getenv(
    "CLINIC_AI_SYSTEM_PROMPT",
    """
Você é uma recepcionista profissional de uma clínica odontológica no Brasil.

Objetivo: atender via WhatsApp de forma humana, educada e objetiva, ajudando o paciente a:
- tirar dúvidas sobre procedimentos,
- agendar ou remarcar consultas,
- orientar próximos passos.

Regras:
- Não invente preços, diagnósticos ou promessas médicas.
- Se faltar informação, faça perguntas curtas.
- Sempre que possível, finalize com uma pergunta para avançar.
""".strip(),
)

DEFAULT_PROCEDURES = {
    "aplicação de resina": {
        "aliases": ["resina", "restauração", "restauracao"],
        "description": "A aplicação de resina (restauração) é indicada para corrigir cáries pequenas, fraturas ou estética. O dentista remove a parte comprometida, prepara o dente e aplica a resina em camadas, modelando e polindo para ficar natural.",
        "duration_min": 60,
    },
    "botox": {
        "aliases": ["botox", "toxina botulínica", "toxina botulinica"],
        "description": "O botox (toxina botulínica) pode ser utilizado para fins estéticos e, em alguns casos, para auxiliar em bruxismo e dor muscular. O profissional avalia, define os pontos de aplicação e realiza microinjeções. As orientações pós-procedimento variam conforme o caso.",
        "duration_min": 30,
    },
    "limpeza de dente": {
        "aliases": ["limpeza", "profilaxia"],
        "description": "A limpeza (profilaxia) remove placa bacteriana e tártaro, ajudando a prevenir gengivite e mau hálito. Normalmente inclui avaliação, remoção de tártaro, polimento e orientações de higiene.",
        "duration_min": 40,
    },
    "clareamento": {
        "aliases": ["clareamento", "branqueamento"],
        "description": "O clareamento dental pode ser feito em consultório e/ou com moldeiras em casa, conforme avaliação. O dentista analisa a saúde bucal, orienta o método ideal e acompanha para segurança e melhor resultado.",
        "duration_min": 60,
    },
}


def _get_clinic_ai_config(clinic_id: int):
    """Retorna configurações de IA. Se a clínica não tiver config, usa padrão."""
    clinic = Clinic.query.get(clinic_id)
    if not clinic:
        return {
            "enabled": False,
            "model": DEFAULT_OPENAI_MODEL,
            "temperature": DEFAULT_TEMPERATURE,
            "system_prompt": DEFAULT_SYSTEM_PROMPT,
            "procedures": DEFAULT_PROCEDURES,
            "booking_policy": "",
            "clinic_name": "",
        }

    # ⚠️ em bancos desatualizados, alguns campos podem não existir ainda.
    enabled = bool(getattr(clinic, "ai_enabled", True))
    model = (getattr(clinic, "ai_model", None) or DEFAULT_OPENAI_MODEL).strip()
    temperature = float(getattr(clinic, "ai_temperature", None) or DEFAULT_TEMPERATURE)
    system_prompt = (getattr(clinic, "ai_system_prompt", None) or DEFAULT_SYSTEM_PROMPT).strip()

    # Compatibilidade: já existiram nomes diferentes.
    procs = getattr(clinic, "ai_procedures", None)
    if not isinstance(procs, dict) or not procs:
        procs = getattr(clinic, "ai_procedures_json", None)

    procedures = procs if isinstance(procs, dict) and procs else DEFAULT_PROCEDURES

    return {
        "enabled": enabled,
        "model": model,
        "temperature": temperature,
        "system_prompt": system_prompt,
        "procedures": procedures,
        "booking_policy": (getattr(clinic, "ai_booking_policy", None) or "").strip(),
        "clinic_name": (getattr(clinic, "name", None) or "").strip(),
    }


def _append_history(data: dict, role: str, content: str, max_items: int = 12):
    if not isinstance(data, dict):
        return
    hist = data.get("history")
    if not isinstance(hist, list):
        hist = []
    hist.append({"role": role, "content": (content or "").strip()[:1500]})
    data["history"] = hist[-max_items:]


def _ai_reply(clinic_id: int, user_text: str, data: dict, push_name: str):
    cfg = _get_clinic_ai_config(clinic_id)
    if not cfg.get("enabled"):
        return None

    # contexto curto + histórico recente
    clinic = Clinic.query.get(clinic_id)
    clinic_name = getattr(clinic, "name", "") if clinic else ""
    context = f"Nome da clínica: {clinic_name}. Nome do paciente: {push_name}."

    # ✅ Enriquecimento do prompt com procedimentos e políticas (editáveis no painel)
    procedures = cfg.get("procedures") or {}
    booking_policy = cfg.get("booking_policy") or ""

    system_blocks = [cfg.get("system_prompt") or DEFAULT_SYSTEM_PROMPT, context]
    if booking_policy:
        system_blocks.append("POLÍTICAS DE AGENDAMENTO (obrigatório seguir):\n" + str(booking_policy).strip())
    if isinstance(procedures, dict) and procedures:
        system_blocks.append(
            "PROCEDIMENTOS (use para explicar de forma simples e profissional; não invente valores/garantias):\n"
            + json.dumps(procedures, ensure_ascii=False, indent=2)
        )

    messages = [{"role": "system", "content": "\n\n".join(system_blocks)}]
    hist = data.get("history") if isinstance(data, dict) else None
    if isinstance(hist, list):
        # já vem no formato role/content
        for item in hist[-10:]:
            if isinstance(item, dict) and item.get("role") in ("user", "assistant"):
                messages.append({"role": item["role"], "content": str(item.get("content", ""))[:1500]})

    try:
        out = chat_reply(
            system_prompt="\n\n".join(system_blocks),
            user_text=user_text,
            history={
                # histórico apenas (não repete a mensagem atual)
                "messages": messages[1:],
                "model": cfg["model"],
                "temperature": cfg["temperature"],
                "max_tokens": 280,
            },
        )
        return (out or "").strip() or None
    except Exception as e:
        logger.warning(f"⚠️ OpenAI falhou: {e}")
        return None

# Estados da Máquina de Estados
STATE_START = 'start'
STATE_AWAITING_DATE = 'awaiting_date'
STATE_AWAITING_TIME = 'awaiting_time'
STATE_AWAITING_CONFIRM = 'awaiting_confirm'
STATE_DONE = 'done'

# ✅ NOVO: Remarcação
STATE_RESCHEDULE_AWAITING_DATE = 'reschedule_awaiting_date'
STATE_RESCHEDULE_AWAITING_TIME = 'reschedule_awaiting_time'
STATE_RESCHEDULE_AWAITING_CONFIRM = 'reschedule_awaiting_confirm'


def get_or_create_session(clinic_id, sender_id):
    session = ChatSession.query.filter_by(clinic_id=clinic_id, sender_id=sender_id).first()
    if not session:
        session = ChatSession(clinic_id=clinic_id, sender_id=sender_id, state=STATE_START, data={})
        db.session.add(session)
        db.session.commit()
    return session


def _is_yes(text: str) -> bool:
    return any(w in text for w in ['sim', 'confirmar', 'pode', 'ok', 'com certeza', 'claro', 'confirmado', 'isso', 'isso mesmo'])

def _is_no(text: str) -> bool:
    return any(w in text for w in ['não', 'nao', 'mudar', 'cancelar', 'errado', 'negativo'])

def _wants_schedule(text: str) -> bool:
    return any(w in text for w in ['agendar', 'consulta', 'marcar', 'avaliação', 'avaliacao'])

def _wants_reschedule(text: str) -> bool:
    return any(w in text for w in ['remarcar', 'reagendar', 'reagendamento', 'mudar horario', 'mudar horário', 'mudar data', 'trocar', 'alterar horario', 'alterar horário', 'alterar data'])


def process_chatbot_message(clinic_id, sender_id, message_text, push_name):
    trace_id = str(uuid.uuid4())[:8]
    session = get_or_create_session(clinic_id, sender_id)
    state = session.state
    data = session.data or {}
    if not isinstance(data, dict):
        data = {}

    logger.info(f"[{trace_id}] Chatbot: clinic={clinic_id} sender={sender_id} state={state} msg={message_text}")

    # Normalização básica
    original_text = (message_text or "").strip()
    text = original_text.lower()
    reply = None

    # ✅ salva histórico do usuário (para a IA responder com contexto)
    _append_history(data, "user", original_text)

    # ✅ qualquer momento: se o cliente pedir remarcar, entra no fluxo de remarcação
    if _wants_reschedule(text):
        # tenta achar um appointment mais recente desse lead/paciente
        appt = _find_last_appointment(clinic_id, sender_id)
        if not appt:
            session.state = STATE_AWAITING_DATE
            data = {}
            reply = "Claro! Não encontrei um agendamento anterior para remarcar. Para qual dia você gostaria de agendar?"
        else:
            data = data or {}
            data['reschedule_appointment_id'] = appt.id
            data.pop('date', None)
            data.pop('time', None)
            session.state = STATE_RESCHEDULE_AWAITING_DATE
            reply = "Claro! Vamos remarcar sua consulta. Para qual dia você gostaria?"

        session.data = data
        db.session.commit()
        if reply:
            _send_whatsapp_reply(clinic_id, sender_id, reply)
        return

    # --------------------
    # Fluxo normal
    # --------------------
    if state == STATE_START:
        if _wants_schedule(text):
            session.state = STATE_AWAITING_DATE
            data = {}
            reply = f"Olá {push_name}! Com certeza 😊 Para qual dia você gostaria de agendar?"
        else:
            # ✅ Atendimento inteligente (ChatGPT) para perguntas gerais
            # (mantemos o fluxo de agendamento por máquina de estados para confiabilidade)
            # ✅ IA (ChatGPT) para atendimento humanizado quando não é agendamento/remarcação.
            # A função helper deste módulo é _ai_reply(clinic_id, user_text, data, push_name)
            # (mantemos o fallback caso a IA esteja desativada/sem chave).
            ai = _ai_reply(clinic_id=clinic_id, user_text=text, data=data, push_name=push_name)
            if ai:
                reply = ai
            else:
                # 🔻 fallback humano se IA estiver desativada ou sem OPENAI_API_KEY
                reply = (
                    f"Olá {push_name}! 😊 No momento vou encaminhar sua mensagem para um atendente humano. "
                    "Enquanto isso, você quer *agendar* ou *remarcar* uma consulta?"
                )

    elif state == STATE_AWAITING_DATE:
        parsed_date = parse_pt_br_date(text)
        if parsed_date:
            data['date'] = parsed_date.strftime('%Y-%m-%d')

            parsed_time = parse_pt_br_time(text)
            if parsed_time:
                data['time'] = parsed_time
                session.state = STATE_AWAITING_CONFIRM
                reply = f"Entendido! Para {parsed_date.strftime('%d/%m')} às {parsed_time}. Podemos confirmar?"
            else:
                session.state = STATE_AWAITING_TIME
                reply = f"Ótimo! Dia {parsed_date.strftime('%d/%m')}. Qual horário você prefere? (Ex: 10h, 15:30)"
        else:
            reply = "Não consegui entender a data. Pode me dizer o dia? (Ex: amanhã, quarta, ou 04/02)"

    elif state == STATE_AWAITING_TIME:
        parsed_time = parse_pt_br_time(text)
        if parsed_time:
            data['time'] = parsed_time
            session.state = STATE_AWAITING_CONFIRM
            date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
            reply = f"Perfeito! Agendamento para {date_obj.strftime('%d/%m')} às {parsed_time}. Confirma?"
        else:
            reply = "Não entendi o horário. Pode me dizer as horas? (Ex: 15h, 15:30 ou apenas 15)"

    elif state == STATE_AWAITING_CONFIRM:
        if _is_yes(text):
            # ✅ proteção: evita 500 por falta de chaves no JSON
            if not data.get("date"):
                session.state = STATE_AWAITING_DATE
                reply = "Perfeito 😊 Só me diga a *data* do agendamento (ex: 10/02, amanhã, quinta)."
            elif not data.get("time"):
                session.state = STATE_AWAITING_TIME
                reply = "Perfeito 😊 Só me diga o *horário* (ex: 10h, 15:30)."
            else:
                result = create_real_appointment(clinic_id, sender_id, data, push_name)
                if result.get("ok"):
                    session.state = STATE_DONE
                    reply = result.get("message") or "Agendamento realizado com sucesso! Te esperamos lá. 😊"
                else:
                    if result.get("reason") == "conflict" and result.get("alternatives"):
                        # mantém a data e pede novo horário
                        data.pop("time", None)
                        session.state = STATE_AWAITING_TIME
                        reply = result.get("message")
                    else:
                        reply = result.get("message") or "Houve um erro ao salvar seu agendamento no sistema. Um atendente humano falará com você em breve."
        elif _is_no(text):
            session.state = STATE_START
            data = {}
            reply = "Sem problemas 😊 Você quer *agendar* ou *remarcar*?"
        else:
            reply = "Por favor, responda com *Sim* para confirmar ou *Não* para recomeçar."

    elif state == STATE_DONE:
        # ✅ depois de concluído, se falar agendar, recomeça
        if _wants_schedule(text):
            session.state = STATE_AWAITING_DATE
            data = {}
            reply = "Vamos lá! Para qual dia você gostaria de agendar uma nova consulta?"
        else:
            # mantém resposta curta para não ser “chato”
            reply = "Certo 😊 Se quiser, você pode dizer *agendar* ou *remarcar*."

    # --------------------
    # Fluxo de remarcação
    # --------------------
    elif state == STATE_RESCHEDULE_AWAITING_DATE:
        parsed_date = parse_pt_br_date(text)
        if parsed_date:
            data['date'] = parsed_date.strftime('%Y-%m-%d')
            parsed_time = parse_pt_br_time(text)
            if parsed_time:
                data['time'] = parsed_time
                session.state = STATE_RESCHEDULE_AWAITING_CONFIRM
                reply = f"Entendido! Remarcar para {parsed_date.strftime('%d/%m')} às {parsed_time}. Confirma?"
            else:
                session.state = STATE_RESCHEDULE_AWAITING_TIME
                reply = f"Ótimo! Dia {parsed_date.strftime('%d/%m')}. Qual horário você prefere?"
        else:
            reply = "Não consegui entender a data. Pode me dizer o dia? (Ex: amanhã, quinta, ou 04/02)"

    elif state == STATE_RESCHEDULE_AWAITING_TIME:
        parsed_time = parse_pt_br_time(text)
        if parsed_time:
            data['time'] = parsed_time
            session.state = STATE_RESCHEDULE_AWAITING_CONFIRM
            date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
            reply = f"Perfeito! Remarcar para {date_obj.strftime('%d/%m')} às {parsed_time}. Confirma?"
        else:
            reply = "Não entendi o horário. Pode me dizer as horas? (Ex: 15h, 15:30)"

    elif state == STATE_RESCHEDULE_AWAITING_CONFIRM:
        if _is_yes(text):
            # ✅ proteção: evita 500 por falta de chaves no JSON
            if not data.get("date"):
                session.state = STATE_RESCHEDULE_AWAITING_DATE
                reply = "Perfeito 😊 Só me diga a *data* para remarcar (ex: 10/02, amanhã, quinta)."
            elif not data.get("time"):
                session.state = STATE_RESCHEDULE_AWAITING_TIME
                reply = "Perfeito 😊 Só me diga o *horário* para remarcar (ex: 10h, 15:30)."
            else:
                appt_id = data.get('reschedule_appointment_id')
                result = reschedule_real_appointment(clinic_id, sender_id, appt_id, data, push_name)
                if result.get("ok"):
                    session.state = STATE_DONE
                    reply = result.get("message") or "Remarcação realizada com sucesso! 😊"
                else:
                    if result.get("reason") == "conflict" and result.get("alternatives"):
                        data.pop("time", None)
                        session.state = STATE_RESCHEDULE_AWAITING_TIME
                        reply = result.get("message")
                    else:
                        reply = result.get("message") or "Não consegui remarcar agora. Um atendente humano falará com você em breve."
        elif _is_no(text):
            session.state = STATE_START
            data = {}
            reply = "Sem problemas 😊 Você quer *agendar* ou *remarcar*?"
        else:
            reply = "Por favor, responda com *Sim* para confirmar ou *Não* para recomeçar."

    session.data = data
    db.session.commit()

    if reply:
        _append_history(data, "assistant", reply)
        _send_whatsapp_reply(clinic_id, sender_id, reply)


def parse_pt_br_date(text):
    # ✅ "hoje" consistente em São Paulo
    today = datetime.now(TZ_SP).replace(hour=0, minute=0, second=0, microsecond=0)

    if 'amanhã' in text or 'amanha' in text:
        return (today + timedelta(days=1)).replace(tzinfo=None)
    if 'hoje' in text:
        return today.replace(tzinfo=None)
    if 'depois de amanhã' in text or 'depois de amanha' in text:
        return (today + timedelta(days=2)).replace(tzinfo=None)

    # DD/MM ou DD/MM/YYYY
    match = re.search(r'(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?', text)
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3)) if match.group(3) else today.year
        if year < 100:
            year += 2000
        try:
            return datetime(year, month, day)
        except:
            return None

    meses = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3, 'abril': 4, 'maio': 5, 'junho': 6,
        'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12
    }
    for mes_nome, mes_num in meses.items():
        if mes_nome in text:
            match = re.search(rf'(\d{{1,2}})\s+(?:de\s+)?{mes_nome}', text)
            if match:
                day = int(match.group(1))
                return datetime(today.year, mes_num, day)

    dias_semana = {
        'segunda': 0, 'terça': 1, 'terca': 1, 'quarta': 2, 'quinta': 3, 'sexta': 4,
        'sábado': 5, 'sabado': 5, 'domingo': 6, 'seg': 0, 'ter': 1, 'qua': 2, 'qui': 3, 'sex': 4
    }
    for dia_nome, dia_num in dias_semana.items():
        if re.search(rf'\b{dia_nome}\b', text):
            days_ahead = dia_num - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).replace(tzinfo=None)

    return None


def parse_pt_br_time(text):
    match = re.search(r'(\d{1,2})[:h](\d{2})\b', text)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            return f"{str(hours).zfill(2)}:{str(minutes).zfill(2)}"

    match = re.search(r'(\d{1,2})\s*h\b', text)
    if match:
        hours = int(match.group(1))
        if 0 <= hours <= 23:
            return f"{str(hours).zfill(2)}:00"

    if not re.search(r'\d{1,2}[/-]\d{1,2}', text):
        match = re.search(r'\b(\d{1,2})\b', text)
        if match:
            h = int(match.group(1))
            if 7 <= h <= 20:
                return f"{str(h).zfill(2)}:00"

    return None


def _find_last_appointment(clinic_id, sender_id):
    # tenta por lead e por patient
    lead = Lead.query.filter_by(clinic_id=clinic_id, phone=sender_id).first()
    patient = Patient.query.filter_by(clinic_id=clinic_id, phone=sender_id).first()

    q = Appointment.query.filter_by(clinic_id=clinic_id)
    if patient:
        q = q.filter((Appointment.patient_id == patient.id) | (Appointment.lead_id == (lead.id if lead else None)))
    elif lead:
        q = q.filter(Appointment.lead_id == lead.id)
    else:
        return None

    # pega o mais recente
    return q.order_by(Appointment.start_datetime.desc()).first()


def _make_local_naive_start_end(date_str: str, time_str: str, duration_min: int = 30):
    """
    ✅ Cria datetime NAIVE no fuso de São Paulo (sem tzinfo)
    Isso evita o bug de "dia anterior" quando a UI/front assume local.
    """
    start_str = f"{date_str} {time_str}"
    start_dt = datetime.strptime(start_str, '%Y-%m-%d %H:%M')
    end_dt = start_dt + timedelta(minutes=max(int(duration_min or 30), 15))
    return start_dt, end_dt


def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def _find_conflict(clinic_id: int, start_dt: datetime, end_dt: datetime, exclude_appointment_id: int | None = None):
    q = Appointment.query.filter_by(clinic_id=clinic_id)
    # evita considerar cancelados
    if hasattr(Appointment, "status"):
        q = q.filter(Appointment.status != 'cancelled')
    if exclude_appointment_id:
        q = q.filter(Appointment.id != exclude_appointment_id)

    # janela de busca: somente eventos que podem cruzar
    q = q.filter(Appointment.start_datetime < end_dt).filter(Appointment.end_datetime > start_dt)
    return q.first()


def _suggest_next_slots(clinic_id: int, day: datetime, duration_min: int = 30, limit: int = 3):
    """Sugere próximos horários disponíveis no mesmo dia (08:00–19:00)."""
    duration_min = max(int(duration_min or 30), 15)
    start_day = day.replace(hour=8, minute=0, second=0, microsecond=0)
    end_day = day.replace(hour=19, minute=0, second=0, microsecond=0)

    # começa pelo próximo slot de 30 min
    cursor = day.replace(second=0, microsecond=0)
    # arredonda para próximo 30
    m = cursor.minute
    if m % 30 != 0:
        cursor = cursor + timedelta(minutes=(30 - (m % 30)))

    slots = []
    while cursor < end_day and len(slots) < limit:
        slot_end = cursor + timedelta(minutes=duration_min)
        if slot_end > end_day:
            break
        conflict = _find_conflict(clinic_id, cursor, slot_end)
        if not conflict:
            slots.append((cursor, slot_end))
        cursor = cursor + timedelta(minutes=30)
        if cursor < start_day:
            cursor = start_day
    return slots


def _format_alternatives(alts: list) -> str:
    """Gera texto com sugestões de horários (labels)."""
    try:
        labels = [a.get("label") for a in (alts or []) if isinstance(a, dict) and a.get("label")]
        if not labels:
            return ""
        return " Sugestões: " + ", ".join(labels) + "."
    except Exception:
        return ""


def create_real_appointment(clinic_id, sender_id, data, push_name):
    """Cria agendamento e retorna dict: {ok, reason?, message?, alternatives?}"""
    try:
        # ✅ validação defensiva (evita KeyError e 500)
        if not isinstance(data, dict):
            return {"ok": False, "reason": "invalid_data", "message": "Tive um problema ao ler seus dados. Vamos tentar de novo: qual *data* você prefere?"}
        if not data.get("date"):
            return {"ok": False, "reason": "missing_date", "message": "Qual *data* você prefere? (ex: 10/02, amanhã, quinta)"}
        if not data.get("time"):
            return {"ok": False, "reason": "missing_time", "message": "Qual *horário* você prefere? (ex: 10h, 15:30)"}

        patient = Patient.query.filter_by(clinic_id=clinic_id, phone=sender_id).first()
        lead = Lead.query.filter_by(clinic_id=clinic_id, phone=sender_id).first()

        duration_min = int(data.get('duration_min') or 30)
        start_dt, end_dt = _make_local_naive_start_end(data['date'], data['time'], duration_min)

        conflict = _find_conflict(clinic_id, start_dt, end_dt)
        if conflict:
            alternatives = _suggest_next_slots(clinic_id, start_dt, duration_min, limit=3)
            alt_list = [
                {"start": s.strftime('%Y-%m-%d %H:%M'), "label": s.strftime('%H:%M')}
                for s, _ in alternatives
            ]
            return {
                "ok": False,
                "reason": "conflict",
                "message": "Esse horário já está ocupado." + _format_alternatives(alt_list) + " Qual horário você prefere?",
                "alternatives": alt_list,
            }

        new_app = Appointment(
            clinic_id=clinic_id,
            patient_id=patient.id if patient else None,
            lead_id=lead.id if lead else None,
            title=f"Consulta - {push_name}",
            description="Agendado via WhatsApp (chatbot)",
            status='scheduled',
            start_datetime=start_dt,
            end_datetime=end_dt,
        )
        db.session.add(new_app)
        db.session.flush()

        # ✅ mover lead/status + mover card para etapa Agendado
        if lead:
            lead.status = 'agendado'

        card = CRMCard.query.filter_by(clinic_id=clinic_id, paciente_phone=sender_id, status='open').first()
        stage_agendado = CRMStage.query.filter_by(clinic_id=clinic_id, nome='Agendado').first()
        if stage_agendado and card:
            card.stage_id = stage_agendado.id

        db.session.commit()

        logger.info(
            f"TRACE_LOG: lead_id={lead.id if lead else 'N/A'} appointment_id={new_app.id} "
            f"start={start_dt.isoformat()} end={end_dt.isoformat()}"
        )
        return {"ok": True, "appointment_id": new_app.id, "message": f"Agendamento confirmado ✅ {start_dt.strftime('%d/%m')} às {start_dt.strftime('%H:%M')}. Te esperamos! 😊"}

    except Exception as e:
        logger.error(f"Erro ao criar agendamento: {e}", exc_info=True)
        db.session.rollback()
        return {"ok": False, "reason": "error"}


def reschedule_real_appointment(clinic_id, sender_id, appointment_id, data, push_name):
    try:
        if not appointment_id:
            return {"ok": False, "reason": "missing_id"}

        # ✅ validação defensiva
        if not isinstance(data, dict):
            return {"ok": False, "reason": "invalid_data", "message": "Tive um problema ao ler seus dados. Vamos tentar de novo: qual *data* você prefere?"}
        if not data.get("date"):
            return {"ok": False, "reason": "missing_date", "message": "Qual *data* você prefere para remarcar? (ex: 10/02, amanhã, quinta)"}
        if not data.get("time"):
            return {"ok": False, "reason": "missing_time", "message": "Qual *horário* você prefere para remarcar? (ex: 10h, 15:30)"}

        appt = Appointment.query.filter_by(clinic_id=clinic_id, id=appointment_id).first()
        if not appt:
            return {"ok": False, "reason": "not_found"}

        duration_min = int(data.get('duration_min') or 30)
        start_dt, end_dt = _make_local_naive_start_end(data['date'], data['time'], duration_min)

        conflict = _find_conflict(clinic_id, start_dt, end_dt, exclude_appointment_id=appt.id)
        if conflict:
            alternatives = _suggest_next_slots(clinic_id, start_dt, duration_min, limit=3)
            alt_list = [
                {"start": s.strftime('%Y-%m-%d %H:%M'), "label": s.strftime('%H:%M')}
                for s, _ in alternatives
            ]
            return {
                "ok": False,
                "reason": "conflict",
                "message": "Esse horário já está ocupado." + _format_alternatives(alt_list) + " Qual horário você prefere?",
                "alternatives": alt_list,
            }

        appt.start_datetime = start_dt
        appt.end_datetime = end_dt
        if getattr(appt, "status", None) in (None, "", "pending"):
            appt.status = "scheduled"

        db.session.commit()
        logger.info(f"TRACE_LOG_RESCHEDULE: appointment_id={appt.id} new_start={start_dt.isoformat()}")
        return {"ok": True, "appointment_id": appt.id, "message": f"Remarcação confirmada ✅ {start_dt.strftime('%d/%m')} às {start_dt.strftime('%H:%M')}."}

    except Exception as e:
        logger.error(f"Erro ao remarcar agendamento: {e}", exc_info=True)
        db.session.rollback()
        return {"ok": False, "reason": "error"}
