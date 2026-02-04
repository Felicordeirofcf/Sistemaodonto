import logging
import json
import uuid
import re
from datetime import datetime, timedelta
from app.models import db, ChatSession, Appointment, Patient, Lead, Clinic
from .webhook import _send_whatsapp_reply

logger = logging.getLogger(__name__)

# Estados da Máquina de Estados
STATE_START = 'start'
STATE_AWAITING_DATE = 'awaiting_date'
STATE_AWAITING_TIME = 'awaiting_time'
STATE_AWAITING_CONFIRM = 'awaiting_confirm'
STATE_DONE = 'done'

def get_or_create_session(clinic_id, sender_id):
    session = ChatSession.query.filter_by(clinic_id=clinic_id, sender_id=sender_id).first()
    if not session:
        session = ChatSession(clinic_id=clinic_id, sender_id=sender_id, state=STATE_START, data={})
        db.session.add(session)
        db.session.commit()
    return session

def process_chatbot_message(clinic_id, sender_id, message_text, push_name):
    trace_id = str(uuid.uuid4())[:8]
    session = get_or_create_session(clinic_id, sender_id)
    state = session.state
    data = session.data or {}
    
    logger.info(f"[{trace_id}] Chatbot: clinic={clinic_id} sender={sender_id} state={state} msg={message_text}")
    
    # Normalização básica
    text = message_text.strip().lower()
    reply = None
    
    if state == STATE_START:
        if any(word in text for word in ['agendar', 'consulta', 'marcar', 'avaliação']):
            session.state = STATE_AWAITING_DATE
            reply = f"Olá {push_name}! Com certeza, vamos agendar sua consulta. Para qual dia você gostaria?"
        else:
            # Se não for intenção de agendamento, mantém no start ou dá boas vindas
            reply = f"Olá {push_name}, bem-vindo à nossa clínica! Como posso te ajudar hoje? Você pode dizer 'Agendar consulta' para começar."
            
    elif state == STATE_AWAITING_DATE:
        parsed_date = parse_pt_br_date(text)
        if parsed_date:
            data['date'] = parsed_date.strftime('%Y-%m-%d')
            # Verifica se já mandou a hora junto (ex: "amanhã as 15h")
            parsed_time = parse_pt_br_time(text)
            if parsed_time:
                data['time'] = parsed_time
                session.state = STATE_AWAITING_CONFIRM
                reply = f"Entendido! Para {parsed_date.strftime('%d/%m')} às {parsed_time}. Podemos confirmar?"
            else:
                session.state = STATE_AWAITING_TIME
                reply = f"Ótimo, dia {parsed_date.strftime('%d/%m')}. Qual o melhor horário?"
        else:
            reply = "Não consegui entender a data. Pode me dizer o dia? (Ex: amanhã, terça, ou 04/02)"
            
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
        if any(word in text for word in ['sim', 'confirmar', 'pode', 'ok', 'com certeza', 'claro', 'confirmado']):
            # Criar agendamento real
            success = create_real_appointment(clinic_id, sender_id, data, push_name)
            if success:
                session.state = STATE_DONE
                reply = "Agendamento realizado com sucesso! Te esperamos lá. 😊"
            else:
                reply = "Houve um erro ao salvar seu agendamento no sistema. Um atendente humano falará com você em breve."
        elif any(word in text for word in ['não', 'nao', 'mudar', 'cancelar', 'errado']):
            session.state = STATE_START
            data = {}
            reply = "Sem problemas. O que você gostaria de fazer agora? Você pode tentar agendar novamente dizendo 'Agendar'."
        else:
            reply = "Por favor, responda com 'Sim' para confirmar ou 'Não' para recomeçar."
            
    elif state == STATE_DONE:
        if any(word in text for word in ['agendar', 'consulta']):
            session.state = STATE_AWAITING_DATE
            data = {}
            reply = "Vamos lá! Para qual dia você gostaria de agendar uma nova consulta?"
        else:
            # Se já terminou, não responde mais automaticamente para não ser chato
            return
            
    session.data = data
    db.session.commit()
    
    if reply:
        _send_whatsapp_reply(clinic_id, sender_id, reply)

def parse_pt_br_date(text):
    # Usar data local de São Paulo para evitar problemas de virada de dia em UTC
    # Como não temos pytz instalado por padrão em todos os ambientes, usamos o offset manual ou datetime.now()
    # mas garantindo que o "hoje" seja consistente.
    today = datetime.now()
    
    # Termos relativos
    if 'amanhã' in text or 'amanha' in text:
        return today + timedelta(days=1)
    if 'hoje' in text:
        return today
    if 'depois de amanhã' in text or 'depois de amanha' in text:
        return today + timedelta(days=2)
        
    # Regex para DD/MM ou DD/MM/YYYY
    match = re.search(r'(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?', text)
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3)) if match.group(3) else today.year
        if year < 100: year += 2000
        try: return datetime(year, month, day)
        except: return None
        
    # Regex para "X de mês"
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
                
    # Dias da semana
    dias_semana = {
        'segunda': 0, 'terça': 1, 'terca': 1, 'quarta': 2, 'quinta': 3, 'sexta': 4, 
        'sábado': 5, 'sabado': 5, 'domingo': 6, 'seg': 0, 'ter': 1, 'qua': 2, 'qui': 3, 'sex': 4
    }
    for dia_nome, dia_num in dias_semana.items():
        # Verifica se a palavra está isolada ou no início/fim
        if re.search(rf'\b{dia_nome}\b', text):
            days_ahead = dia_num - today.weekday()
            if days_ahead <= 0: days_ahead += 7
            return today + timedelta(days=days_ahead)
            
    return None

def parse_pt_br_time(text):
    # 15:30 ou 15h30 ou 15h ou 15:00
    # Melhoria: Capturar "10", "10h", "10:00" sem cair em 00:00
    
    # 1) Tenta formato HH:MM ou HHhMM
    match = re.search(r'(\d{1,2})[:h](\d{2})\b', text)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            return f"{str(hours).zfill(2)}:{str(minutes).zfill(2)}"
            
    # 2) Tenta formato "10h" ou "10 h"
    match = re.search(r'(\d{1,2})\s*h\b', text)
    if match:
        hours = int(match.group(1))
        if 0 <= hours <= 23:
            return f"{str(hours).zfill(2)}:00"

    # 3) Apenas o número se for entre 7 e 20 (horário comercial)
    # Evita pegar números que pareçam datas (DD/MM)
    if not re.search(r'\d{1,2}[/-]\d{1,2}', text):
        match = re.search(r'\b(\d{1,2})\b', text)
        if match:
            h = int(match.group(1))
            if 7 <= h <= 20:
                return f"{str(h).zfill(2)}:00"
            
    return None

def create_real_appointment(clinic_id, sender_id, data, push_name):
    try:
        # Tenta achar paciente pelo telefone
        patient = Patient.query.filter_by(clinic_id=clinic_id, phone=sender_id).first()
        
        # Se não existe, tenta achar lead
        lead = Lead.query.filter_by(clinic_id=clinic_id, phone=sender_id).first()
        
        start_str = f"{data['date']} {data['time']}"
        start_dt = datetime.strptime(start_str, '%Y-%m-%d %H:%M')
        end_dt = start_dt + timedelta(minutes=30)
        
        new_app = Appointment(
            clinic_id=clinic_id,
            patient_id=patient.id if patient else None,
            lead_id=lead.id if lead else None,
            title=f"Consulta - {push_name}",
            start_datetime=start_dt,
            end_datetime=end_dt,
            status='scheduled'
        )
        db.session.add(new_app)

        # Problema 1: Mover Lead e Card no CRM
        if lead:
            lead.status = 'agendado'
            logger.info(f"Lead {lead.id} atualizado para status 'agendado'")
            
            # Mover Card no CRM
            from app.models import CRMCard, CRMStage, CRMHistory
            card = CRMCard.query.filter_by(clinic_id=clinic_id, paciente_phone=sender_id, status='open').first()
            if card:
                stage_agendado = CRMStage.query.filter_by(clinic_id=clinic_id, nome='Agendado').first()
                if not stage_agendado:
                    # Criar etapa se não existir
                    stage_agendado = CRMStage(
                        clinic_id=clinic_id, 
                        nome='Agendado', 
                        cor='green', 
                        ordem=10, 
                        is_success=True
                    )
                    db.session.add(stage_agendado)
                    db.session.flush()
                
                if stage_agendado:
                    card.stage_id = stage_agendado.id
                    # Registrar atividade
                    history = CRMHistory(
                        card_id=card.id,
                        tipo='status_change',
                        descricao=f"Agendamento criado via Chatbot para {start_dt.strftime('%d/%m/%Y %H:%M')}"
                    )
                    db.session.add(history)
                    logger.info(f"Card {card.id} movido para etapa 'Agendado'")

        db.session.commit()
        
        # Log final conforme solicitado
        logger.info(f"TRACE_LOG: lead_id={lead.id if lead else 'N/A'} appointment_id={new_app.id} start_datetime={start_dt.isoformat()}")
        
        return True
    except Exception as e:
        logger.error(f"Erro ao criar agendamento: {e}")
        db.session.rollback()
        return False
