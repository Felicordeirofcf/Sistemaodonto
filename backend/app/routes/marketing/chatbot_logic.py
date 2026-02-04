import logging
import json
import uuid
import re
from datetime import datetime, timedelta

# ✅ timezone robusto (Python 3.9+)
from zoneinfo import ZoneInfo

from app.models import db, ChatSession, Appointment, Patient, Lead, Clinic, CRMCard, CRMStage
from .webhook import _send_whatsapp_reply

logger = logging.getLogger(__name__)

TZ_SP = ZoneInfo("America/Sao_Paulo")

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

    logger.info(f"[{trace_id}] Chatbot: clinic={clinic_id} sender={sender_id} state={state} msg={message_text}")

    # Normalização básica
    text = (message_text or "").strip().lower()
    reply = None

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
            reply = f"Olá {push_name}, bem-vindo(a) à nossa clínica! 😊 Você quer *agendar* ou *remarcar* uma consulta?"

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
            success = create_real_appointment(clinic_id, sender_id, data, push_name)
            if success:
                session.state = STATE_DONE
                reply = "Agendamento realizado com sucesso! Te esperamos lá. 😊"
            else:
                reply = "Houve um erro ao salvar seu agendamento no sistema. Um atendente humano falará com você em breve."
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
            appt_id = data.get('reschedule_appointment_id')
            success = reschedule_real_appointment(clinic_id, sender_id, appt_id, data, push_name)
            if success:
                session.state = STATE_DONE
                reply = "Remarcação realizada com sucesso! 😊"
            else:
                reply = "Não consegui remarcar agora. Um atendente humano falará com você em breve."
        elif _is_no(text):
            session.state = STATE_START
            data = {}
            reply = "Sem problemas 😊 Você quer *agendar* ou *remarcar*?"
        else:
            reply = "Por favor, responda com *Sim* para confirmar ou *Não* para recomeçar."

    session.data = data
    db.session.commit()

    if reply:
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

    # pega o mais recente (se existir start_datetime, usa ele; caso contrário date_time)
    appt = q.order_by(getattr(Appointment, "start_datetime", Appointment.date_time).desc()).first()
    return appt


def _make_local_naive_start_end(date_str: str, time_str: str):
    """
    ✅ Cria datetime NAIVE no fuso de São Paulo (sem tzinfo)
    Isso evita o bug de "dia anterior" quando a UI/front assume local.
    """
    start_str = f"{date_str} {time_str}"
    start_dt = datetime.strptime(start_str, '%Y-%m-%d %H:%M')
    end_dt = start_dt + timedelta(minutes=30)
    return start_dt, end_dt


def create_real_appointment(clinic_id, sender_id, data, push_name):
    try:
        patient = Patient.query.filter_by(clinic_id=clinic_id, phone=sender_id).first()
        lead = Lead.query.filter_by(clinic_id=clinic_id, phone=sender_id).first()

        start_dt, end_dt = _make_local_naive_start_end(data['date'], data['time'])

        # ✅ Preenche campos que existem na SUA tabela (screenshot):
        # - date_time (NOT NULL)
        # - patient_name, procedure, status, start_datetime, end_datetime, title/description
        new_app = Appointment(
            clinic_id=clinic_id,
            patient_id=patient.id if patient else None,
            lead_id=lead.id if lead else None,
            patient_name=push_name,
            procedure="Consulta",
            title=f"Consulta - {push_name}",
            description="Agendado via WhatsApp (chatbot)",
            status='scheduled',
            date_time=start_dt,          # ✅ importante: NOT NULL
            start_datetime=start_dt,     # ✅ para telas/queries que usam start_datetime
            end_datetime=end_dt
        )
        db.session.add(new_app)
        db.session.flush()  # garante new_app.id sem precisar commit ainda

        # ✅ mover lead/status + mover card para etapa Agendado
        if lead:
            lead.status = 'agendado'

        card = CRMCard.query.filter_by(clinic_id=clinic_id, paciente_phone=sender_id, status='open').first()
        stage_agendado = CRMStage.query.filter_by(clinic_id=clinic_id, nome='Agendado').first()
        if stage_agendado and card:
            card.stage_id = stage_agendado.id

        db.session.commit()

        logger.info(
            f"TRACE_LOG: lead_id={lead.id if lead else 'N/A'} "
            f"appointment_id={new_app.id} start={start_dt.isoformat()} end={end_dt.isoformat()}"
        )
        return True

    except Exception as e:
        logger.error(f"Erro ao criar agendamento: {e}", exc_info=True)
        db.session.rollback()
        return False


def reschedule_real_appointment(clinic_id, sender_id, appointment_id, data, push_name):
    try:
        if not appointment_id:
            return False

        appt = Appointment.query.filter_by(clinic_id=clinic_id, id=appointment_id).first()
        if not appt:
            return False

        start_dt, end_dt = _make_local_naive_start_end(data['date'], data['time'])

        # ✅ atualiza campos principais (incluindo date_time NOT NULL)
        appt.date_time = start_dt
        if hasattr(appt, "start_datetime"):
            appt.start_datetime = start_dt
        if hasattr(appt, "end_datetime"):
            appt.end_datetime = end_dt

        # mantém status
        if getattr(appt, "status", None) in (None, "", "pending"):
            appt.status = "scheduled"

        db.session.commit()
        logger.info(f"TRACE_LOG_RESCHEDULE: appointment_id={appt.id} new_start={start_dt.isoformat()}")
        return True

    except Exception as e:
        logger.error(f"Erro ao remarcar agendamento: {e}", exc_info=True)
        db.session.rollback()
        return False
