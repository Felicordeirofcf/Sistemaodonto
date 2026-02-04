import logging
import uuid
import re
from datetime import datetime, timedelta

from zoneinfo import ZoneInfo

from app.models import db, ChatSession, Appointment, Patient, Lead, Clinic, CRMCard, CRMStage
from .webhook import _send_whatsapp_reply

logger = logging.getLogger(__name__)
TZ_SP = ZoneInfo("America/Sao_Paulo")

# ---------------------------------------------------------------------------
# Estados (máquina de estados)
# ---------------------------------------------------------------------------
STATE_START = "start"
STATE_AWAITING_PROCEDURE = "awaiting_procedure"
STATE_AWAITING_DATE = "awaiting_date"
STATE_AWAITING_TIME = "awaiting_time"
STATE_AWAITING_CONFIRM = "awaiting_confirm"
STATE_DONE = "done"

# Remarcação
STATE_RESCHEDULE_AWAITING_DATE = "reschedule_awaiting_date"
STATE_RESCHEDULE_AWAITING_TIME = "reschedule_awaiting_time"
STATE_RESCHEDULE_AWAITING_CONFIRM = "reschedule_awaiting_confirm"

# ---------------------------------------------------------------------------
# Catálogo default (pode ser sobrescrito por Clinic.services_catalog)
# Estrutura: {"chave": {"nome": "...", "desc": "...", "duracao_min": 30}}
# ---------------------------------------------------------------------------
DEFAULT_SERVICES = {
    "aplicacao_resina": {
        "nome": "Aplicação de resina",
        "desc": (
            "A resina composta é usada para restaurar dentes com cáries pequenas, fraturas ou para ajustes estéticos. "
            "O procedimento costuma ser rápido e minimamente invasivo, feito no consultório."
        ),
        "duracao_min": 40,
    },
    "botox": {
        "nome": "Botox",
        "desc": (
            "Aplicação de toxina botulínica para fins estéticos e/ou funcionais (ex.: bruxismo). "
            "Inclui avaliação prévia e orientações de pós-procedimento."
        ),
        "duracao_min": 30,
    },
    "limpeza": {
        "nome": "Limpeza (profilaxia)",
        "desc": (
            "Remoção de placa bacteriana e tártaro, polimento e orientações de higiene. "
            "Ajuda a prevenir gengivite, mau hálito e cáries."
        ),
        "duracao_min": 40,
    },
    "clareamento": {
        "nome": "Clareamento dental",
        "desc": (
            "Clareamento pode ser feito em consultório e/ou com moldeiras (caseiro supervisionado). "
            "A indicação depende de avaliação do dentista para segurança e melhor resultado."
        ),
        "duracao_min": 60,
    },
    "consulta": {
        "nome": "Consulta / avaliação",
        "desc": "Avaliação inicial para entender sua necessidade e indicar o melhor plano de tratamento.",
        "duracao_min": 30,
    },
}

# Palavras-chave -> chave do serviço
SERVICE_KEYWORDS = {
    "resina": "aplicacao_resina",
    "restaur": "aplicacao_resina",
    "botox": "botox",
    "toxina": "botox",
    "limpeza": "limpeza",
    "profilax": "limpeza",
    "tartaro": "limpeza",
    "tártaro": "limpeza",
    "clareamento": "clareamento",
    "clarear": "clareamento",
    "avaliacao": "consulta",
    "avaliação": "consulta",
    "consulta": "consulta",
}

# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------
def _only_digits(value: str) -> str:
    return "".join(filter(str.isdigit, value or ""))

def get_or_create_session(clinic_id: int, sender_id: str) -> ChatSession:
    # normaliza sender para número (caso venha com @lid etc)
    sender_norm = _only_digits(sender_id) or sender_id

    session = ChatSession.query.filter_by(clinic_id=clinic_id, sender_id=sender_norm).first()
    if not session:
        session = ChatSession(clinic_id=clinic_id, sender_id=sender_norm, state=STATE_START, data={})
        db.session.add(session)
        db.session.commit()
    return session

# ---------------------------------------------------------------------------
# Intents
# ---------------------------------------------------------------------------
def _is_yes(text: str) -> bool:
    t = (text or "").lower()
    return any(w in t for w in ["sim", "confirmar", "pode", "ok", "com certeza", "claro", "confirmado", "isso", "isso mesmo"])

def _is_no(text: str) -> bool:
    t = (text or "").lower()
    return any(w in t for w in ["não", "nao", "mudar", "cancelar", "errado", "negativo"])

def _wants_schedule(text: str) -> bool:
    t = (text or "").lower()
    return any(w in t for w in ["agendar", "consulta", "marcar", "avaliação", "avaliacao", "horario", "horário"])

def _wants_reschedule(text: str) -> bool:
    t = (text or "").lower()
    return any(w in t for w in ["remarcar", "reagendar", "reagendamento", "mudar horario", "mudar horário", "mudar data", "trocar", "alterar horario", "alterar horário", "alterar data"])

def _wants_info(text: str) -> bool:
    t = (text or "").lower()
    return any(w in t for w in ["o que é", "o que eh", "como funciona", "como é", "como eh", "explica", "explicar", "procedimento", "fazem", "faz"])

def _extract_service_key(text: str) -> str | None:
    t = (text or "").lower()
    for kw, key in SERVICE_KEYWORDS.items():
        if kw in t:
            return key
    return None

# ---------------------------------------------------------------------------
# Parsing pt-BR
# ---------------------------------------------------------------------------
def parse_pt_br_date(text: str):
    today = datetime.now(TZ_SP).replace(hour=0, minute=0, second=0, microsecond=0)

    t = (text or "").lower().strip()

    if "depois de amanhã" in t or "depois de amanha" in t:
        return (today + timedelta(days=2)).replace(tzinfo=None)
    if "amanhã" in t or "amanha" in t:
        return (today + timedelta(days=1)).replace(tzinfo=None)
    if "hoje" in t:
        return today.replace(tzinfo=None)

    # DD/MM ou DD/MM/YYYY
    match = re.search(r"(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?", t)
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3)) if match.group(3) else today.year
        if year < 100:
            year += 2000
        try:
            return datetime(year, month, day)
        except Exception:
            return None

    meses = {
        "janeiro": 1, "fevereiro": 2, "março": 3, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
        "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
    }
    for mes_nome, mes_num in meses.items():
        if mes_nome in t:
            match = re.search(rf"(\d{{1,2}})\s+(?:de\s+)?{mes_nome}", t)
            if match:
                day = int(match.group(1))
                return datetime(today.year, mes_num, day)

    dias_semana = {
        "segunda": 0, "terça": 1, "terca": 1, "quarta": 2, "quinta": 3, "sexta": 4,
        "sábado": 5, "sabado": 5, "domingo": 6, "seg": 0, "ter": 1, "qua": 2, "qui": 3, "sex": 4
    }
    for dia_nome, dia_num in dias_semana.items():
        if re.search(rf"\b{dia_nome}\b", t):
            days_ahead = dia_num - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).replace(tzinfo=None)

    return None


def parse_pt_br_time(text: str):
    t = (text or "").lower().strip()

    # 15:30, 15h30, 15h:30
    match = re.search(r"(\d{1,2})\s*[:h]\s*(\d{2})\b", t)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            return f"{str(hours).zfill(2)}:{str(minutes).zfill(2)}"

    # 15h
    match = re.search(r"(\d{1,2})\s*h\b", t)
    if match:
        hours = int(match.group(1))
        if 0 <= hours <= 23:
            return f"{str(hours).zfill(2)}:00"

    # apenas "15" (se não for data)
    if not re.search(r"\d{1,2}[/-]\d{1,2}", t):
        match = re.search(r"\b(\d{1,2})\b", t)
        if match:
            h = int(match.group(1))
            if 7 <= h <= 20:
                return f"{str(h).zfill(2)}:00"

    return None

# ---------------------------------------------------------------------------
# Agenda helpers (conflitos + sugestão)
# ---------------------------------------------------------------------------
def _get_services_for_clinic(clinic: Clinic) -> dict:
    custom = getattr(clinic, "services_catalog", None) or {}
    if not isinstance(custom, dict):
        custom = {}
    # merge: custom sobrescreve default
    merged = {**DEFAULT_SERVICES, **custom}
    return merged

def _service_duration_min(services: dict, service_key: str) -> int:
    entry = services.get(service_key) or {}
    try:
        return int(entry.get("duracao_min", 30))
    except Exception:
        return 30

def _make_start_end(date_str: str, time_str: str, duration_min: int):
    start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    end_dt = start_dt + timedelta(minutes=duration_min)
    return start_dt, end_dt

def _has_conflict(clinic_id: int, start_dt: datetime, end_dt: datetime, ignore_appt_id: int | None = None) -> bool:
    q = Appointment.query.filter_by(clinic_id=clinic_id)
    if hasattr(Appointment, "status"):
        q = q.filter(Appointment.status != "cancelled")

    if ignore_appt_id:
        q = q.filter(Appointment.id != ignore_appt_id)

    # overlap: start < other_end and end > other_start
    q = q.filter(Appointment.start_datetime < end_dt, Appointment.end_datetime > start_dt)
    return db.session.query(q.exists()).scalar()

def _suggest_next_slots(clinic_id: int, date_obj: datetime, duration_min: int, step_min: int = 30, max_suggestions: int = 3):
    # horário comercial padrão: 08:00 - 19:00 (ajuste se quiser)
    start_day = date_obj.replace(hour=8, minute=0, second=0, microsecond=0)
    end_day = date_obj.replace(hour=19, minute=0, second=0, microsecond=0)

    suggestions = []
    cur = start_day
    while cur + timedelta(minutes=duration_min) <= end_day and len(suggestions) < max_suggestions:
        end = cur + timedelta(minutes=duration_min)
        if not _has_conflict(clinic_id, cur, end):
            suggestions.append(cur.strftime("%H:%M"))
        cur += timedelta(minutes=step_min)

    return suggestions

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
def process_chatbot_message(clinic_id: int, sender_id: str, message_text: str, push_name: str):
    trace_id = str(uuid.uuid4())[:8]

    sender_norm = _only_digits(sender_id) or sender_id
    session = get_or_create_session(clinic_id, sender_norm)
    state = session.state
    data = session.data or {}

    clinic = Clinic.query.get(clinic_id)
    services = _get_services_for_clinic(clinic) if clinic else DEFAULT_SERVICES

    text = (message_text or "").strip()
    text_l = text.lower()

    logger.info(f"[{trace_id}] Chatbot: clinic={clinic_id} sender={sender_norm} state={state} msg={text}")

    # -----------------------------------------------------------------------
    # 1) Remarcação pode entrar a qualquer momento
    # -----------------------------------------------------------------------
    if _wants_reschedule(text_l):
        appt = _find_last_appointment(clinic_id, sender_norm)
        if not appt:
            session.state = STATE_AWAITING_PROCEDURE
            session.data = {}
            db.session.commit()
            _send_whatsapp_reply(clinic_id, sender_norm, "Claro! Não encontrei um agendamento anterior para remarcar. Qual procedimento você gostaria? (ex.: limpeza, resina, clareamento, botox ou consulta)")
            return

        data = {}
        data["reschedule_appointment_id"] = appt.id
        data["service_key"] = _guess_service_key_from_appointment(appt) or "consulta"
        session.state = STATE_RESCHEDULE_AWAITING_DATE
        session.data = data
        db.session.commit()
        _send_whatsapp_reply(clinic_id, sender_norm, "Claro! Vamos remarcar sua consulta. Para qual dia você gostaria?")
        return

    # -----------------------------------------------------------------------
    # 2) Se o cliente pedir info de procedimento (fora do fluxo), responde
    # -----------------------------------------------------------------------
    service_key = _extract_service_key(text_l)
    if service_key and (_wants_info(text_l) or "preço" in text_l or "preco" in text_l):
        entry = services.get(service_key, DEFAULT_SERVICES["consulta"])
        resp = (
            f"Perfeito 😊 *{entry.get('nome', 'Procedimento')}*\n"
            f"{entry.get('desc','')}\n\n"
            f"Se quiser, eu posso *agendar* para você. Qual dia prefere?"
        )
        _send_whatsapp_reply(clinic_id, sender_norm, resp)
        return

    reply = None

    # -----------------------------------------------------------------------
    # 3) Fluxo normal
    # -----------------------------------------------------------------------
    if state == STATE_START:
        if _wants_schedule(text_l):
            # tenta capturar procedimento já na primeira mensagem
            sk = _extract_service_key(text_l) or "consulta"
            data = {"service_key": sk}
            if not _extract_service_key(text_l):
                session.state = STATE_AWAITING_PROCEDURE
                reply = f"Olá {push_name}! 😊 Claro. Qual procedimento você deseja? (ex.: limpeza, resina, clareamento, botox ou consulta)"
            else:
                session.state = STATE_AWAITING_DATE
                entry = services.get(sk, DEFAULT_SERVICES["consulta"])
                reply = f"Olá {push_name}! 😊 Vamos agendar *{entry.get('nome','consulta')}*. Para qual dia você prefere?"
        else:
            reply = f"Olá {push_name}, tudo bem? 😊 Eu sou a recepcionista virtual. Você quer *agendar* ou *remarcar* uma consulta?"

    elif state == STATE_AWAITING_PROCEDURE:
        sk = _extract_service_key(text_l)
        if sk:
            data["service_key"] = sk
            session.state = STATE_AWAITING_DATE
            entry = services.get(sk, DEFAULT_SERVICES["consulta"])
            reply = f"Perfeito! *{entry.get('nome','')}* 👍 Para qual dia você gostaria de agendar?"
        else:
            reply = "Não consegui identificar o procedimento. Você prefere *limpeza*, *resina*, *clareamento*, *botox* ou *consulta*?"

    elif state == STATE_AWAITING_DATE:
        parsed_date = parse_pt_br_date(text_l)
        if parsed_date:
            data["date"] = parsed_date.strftime("%Y-%m-%d")

            # se a pessoa já mandou horário junto
            parsed_time = parse_pt_br_time(text_l)
            if parsed_time:
                data["time"] = parsed_time
                session.state = STATE_AWAITING_CONFIRM
                sk = data.get("service_key", "consulta")
                entry = services.get(sk, DEFAULT_SERVICES["consulta"])
                reply = f"Entendido! *{entry.get('nome','Consulta')}* para {parsed_date.strftime('%d/%m')} às {parsed_time}. Podemos confirmar?"
            else:
                session.state = STATE_AWAITING_TIME
                reply = f"Ótimo! Dia {parsed_date.strftime('%d/%m')}. Qual horário você prefere? (Ex: 10h, 15:30)"
        else:
            reply = "Não consegui entender a data. Pode me dizer o dia? (Ex: amanhã, quinta, ou 04/02)"

    elif state == STATE_AWAITING_TIME:
        parsed_time = parse_pt_br_time(text_l)
        if parsed_time:
            data["time"] = parsed_time
            session.state = STATE_AWAITING_CONFIRM

            date_obj = datetime.strptime(data["date"], "%Y-%m-%d")
            sk = data.get("service_key", "consulta")
            entry = services.get(sk, DEFAULT_SERVICES["consulta"])
            reply = f"Perfeito! *{entry.get('nome','Consulta')}* para {date_obj.strftime('%d/%m')} às {parsed_time}. Confirma?"
        else:
            reply = "Não entendi o horário. Pode me dizer as horas? (Ex: 15h, 15:30 ou apenas 15)"

    elif state == STATE_AWAITING_CONFIRM:
        if _is_yes(text_l):
            sk = data.get("service_key", "consulta")
            duration_min = _service_duration_min(services, sk)
            start_dt, end_dt = _make_start_end(data["date"], data["time"], duration_min)

            # conflito?
            if _has_conflict(clinic_id, start_dt, end_dt):
                date_obj = datetime.strptime(data["date"], "%Y-%m-%d")
                alternatives = _suggest_next_slots(clinic_id, date_obj, duration_min)
                if alternatives:
                    reply = (
                        f"Poxa 😕 já existe uma consulta nesse horário. "
                        f"Você pode escolher um destes horários no mesmo dia: *{', '.join(alternatives)}*?\n"
                        f"(Se preferir, pode me dizer outro dia também.)"
                    )
                    session.state = STATE_AWAITING_TIME
                else:
                    reply = "Poxa 😕 esse dia está bem cheio. Você pode me dizer *outro dia* para eu sugerir horários?"
                    session.state = STATE_AWAITING_DATE
            else:
                success = create_real_appointment(clinic_id, sender_norm, data, push_name, services)
                if success:
                    session.state = STATE_DONE
                    reply = "Agendamento realizado com sucesso! ✅ Te esperamos na clínica. 😊"
                else:
                    reply = "Houve um erro ao salvar seu agendamento. Um atendente humano falará com você em breve."
        elif _is_no(text_l):
            session.state = STATE_START
            data = {}
            reply = "Sem problemas 😊 Você quer *agendar* ou *remarcar*?"
        else:
            reply = "Por favor, responda com *Sim* para confirmar ou *Não* para recomeçar."

    elif state == STATE_DONE:
        if _wants_schedule(text_l):
            session.state = STATE_AWAITING_PROCEDURE
            data = {}
            reply = "Claro! Qual procedimento você deseja agendar agora?"
        else:
            reply = "Certo 😊 Se quiser, você pode dizer *agendar*, *remarcar* ou perguntar sobre um procedimento (ex.: clareamento)."

    # -----------------------------------------------------------------------
    # 4) Fluxo de remarcação
    # -----------------------------------------------------------------------
    elif state == STATE_RESCHEDULE_AWAITING_DATE:
        parsed_date = parse_pt_br_date(text_l)
        if parsed_date:
            data["date"] = parsed_date.strftime("%Y-%m-%d")
            parsed_time = parse_pt_br_time(text_l)
            if parsed_time:
                data["time"] = parsed_time
                session.state = STATE_RESCHEDULE_AWAITING_CONFIRM
                reply = f"Entendido! Remarcar para {parsed_date.strftime('%d/%m')} às {parsed_time}. Confirma?"
            else:
                session.state = STATE_RESCHEDULE_AWAITING_TIME
                reply = f"Ótimo! Dia {parsed_date.strftime('%d/%m')}. Qual horário você prefere?"
        else:
            reply = "Não consegui entender a data. Pode me dizer o dia? (Ex: amanhã, quinta, ou 04/02)"

    elif state == STATE_RESCHEDULE_AWAITING_TIME:
        parsed_time = parse_pt_br_time(text_l)
        if parsed_time:
            data["time"] = parsed_time
            session.state = STATE_RESCHEDULE_AWAITING_CONFIRM
            date_obj = datetime.strptime(data["date"], "%Y-%m-%d")
            reply = f"Perfeito! Remarcar para {date_obj.strftime('%d/%m')} às {parsed_time}. Confirma?"
        else:
            reply = "Não entendi o horário. Pode me dizer as horas? (Ex: 15h, 15:30)"

    elif state == STATE_RESCHEDULE_AWAITING_CONFIRM:
        if _is_yes(text_l):
            appt_id = data.get("reschedule_appointment_id")
            sk = data.get("service_key", "consulta")
            duration_min = _service_duration_min(services, sk)
            success = reschedule_real_appointment(clinic_id, sender_norm, appt_id, data, push_name, duration_min)
            if success:
                session.state = STATE_DONE
                reply = "Remarcação realizada com sucesso! ✅"
            else:
                reply = "Não consegui remarcar agora. Um atendente humano falará com você em breve."
        elif _is_no(text_l):
            session.state = STATE_START
            data = {}
            reply = "Sem problemas 😊 Você quer *agendar* ou *remarcar*?"
        else:
            reply = "Por favor, responda com *Sim* para confirmar ou *Não* para recomeçar."

    session.data = data
    db.session.commit()

    if reply:
        _send_whatsapp_reply(clinic_id, sender_norm, reply)

# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
def _find_last_appointment(clinic_id: int, sender_phone: str):
    lead = Lead.query.filter_by(clinic_id=clinic_id, phone=sender_phone).first()
    patient = Patient.query.filter_by(clinic_id=clinic_id, phone=sender_phone).first()

    q = Appointment.query.filter_by(clinic_id=clinic_id)
    if patient and hasattr(Appointment, "patient_id"):
        q = q.filter((Appointment.patient_id == patient.id) | (Appointment.lead_id == (lead.id if lead else None)))
    elif lead:
        q = q.filter(Appointment.lead_id == lead.id)
    else:
        return None

    return q.order_by(Appointment.start_datetime.desc()).first()

def _guess_service_key_from_appointment(appt: Appointment) -> str | None:
    title = (getattr(appt, "title", "") or "").lower()
    for kw, key in SERVICE_KEYWORDS.items():
        if kw in title:
            return key
    return None

# ---------------------------------------------------------------------------
# Create / Reschedule
# ---------------------------------------------------------------------------
def create_real_appointment(clinic_id: int, sender_phone: str, data: dict, push_name: str, services: dict) -> bool:
    try:
        patient = Patient.query.filter_by(clinic_id=clinic_id, phone=sender_phone).first()
        lead = Lead.query.filter_by(clinic_id=clinic_id, phone=sender_phone).first()

        service_key = data.get("service_key") or "consulta"
        entry = services.get(service_key, DEFAULT_SERVICES["consulta"])
        duration_min = _service_duration_min(services, service_key)

        start_dt, end_dt = _make_start_end(data["date"], data["time"], duration_min)

        # segurança: conflito antes de gravar
        if _has_conflict(clinic_id, start_dt, end_dt):
            return False

        title = f"{entry.get('nome','Consulta')} - {push_name}"
        description = f"Agendado via WhatsApp (chatbot). Procedimento: {entry.get('nome','Consulta')}"

        new_app = Appointment(
            clinic_id=clinic_id,
            patient_id=patient.id if patient else None,
            lead_id=lead.id if lead else None,
            title=title,
            description=description,
            status="scheduled",
            start_datetime=start_dt,
            end_datetime=end_dt,
        )
        db.session.add(new_app)
        db.session.flush()

        # atualizar lead/status + mover card para etapa Agendado
        if lead:
            lead.status = "agendado"

        card = CRMCard.query.filter_by(clinic_id=clinic_id, paciente_phone=sender_phone, status="open").first()
        stage_agendado = CRMStage.query.filter_by(clinic_id=clinic_id, nome="Agendado").first()
        if stage_agendado and card:
            card.stage_id = stage_agendado.id

        db.session.commit()
        return True

    except Exception as e:
        logger.error(f"Erro ao criar agendamento: {e}", exc_info=True)
        db.session.rollback()
        return False


def reschedule_real_appointment(clinic_id: int, sender_phone: str, appointment_id: int, data: dict, push_name: str, duration_min: int) -> bool:
    try:
        if not appointment_id:
            return False

        appt = Appointment.query.filter_by(clinic_id=clinic_id, id=appointment_id).first()
        if not appt:
            return False

        start_dt, end_dt = _make_start_end(data["date"], data["time"], duration_min)

        # conflito (ignorando o próprio)
        if _has_conflict(clinic_id, start_dt, end_dt, ignore_appt_id=appt.id):
            return False

        appt.start_datetime = start_dt
        appt.end_datetime = end_dt

        if getattr(appt, "status", None) in (None, "", "pending"):
            appt.status = "scheduled"

        db.session.commit()
        return True

    except Exception as e:
        logger.error(f"Erro ao remarcar agendamento: {e}", exc_info=True)
        db.session.rollback()
        return False
