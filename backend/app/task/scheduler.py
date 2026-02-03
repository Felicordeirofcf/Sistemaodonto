import os
import requests
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import and_

# Importa o app e o banco
from app import create_app, db
from app.models import (
    AutomacaoRecall, Patient, Appointment, 
    CRMCard, CRMStage, CRMHistory, WhatsAppConnection
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Scheduler")

EVOLUTION_API_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "minha-senha-secreta")

def get_headers():
    return {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }

def enviar_whatsapp_interno(clinic_id, telefone, mensagem):
    instance_name = f"clinica_v3_{clinic_id}"
    phone_number = ''.join(filter(str.isdigit, telefone))
    if len(phone_number) == 11 and not phone_number.startswith("55"):
        phone_number = "55" + phone_number

    url = f"{EVOLUTION_API_URL}/message/sendText/{instance_name}"
    payload = {
        "number": phone_number,
        "text": mensagem,
        "delay": 1200,
        "linkPreview": False
    }

    try:
        r = requests.post(url, json=payload, headers=get_headers(), timeout=30)
        if r.status_code == 201:
            return True, "Enviado"
        else:
            return False, f"Erro API: {r.text}"
    except Exception as e:
        return False, str(e)

def processar_automacoes():
    """
    Roda a cada 1 hora.
    """
    app = create_app()
    with app.app_context():
        # --- CORREÇÃO DE FUSO HORÁRIO (BRASIL GMT-3) ---
        # Pega a hora UTC e diminui 3 horas
        hora_brasil = datetime.utcnow() - timedelta(hours=3)
        hora_formatada = hora_brasil.strftime("%H:00")
        
        logger.info(f"⏰ Scheduler rodando | Hora Brasil: {hora_formatada} | Hora Server (UTC): {datetime.utcnow().strftime('%H:%M')}")

        regras = AutomacaoRecall.query.filter_by(ativo=True).all()

        for regra in regras:
            # Compara com a hora do Brasil
            if regra.horario_disparo and regra.horario_disparo.startswith(hora_formatada[:2]):
                logger.info(f"🚀 Executando regra '{regra.nome}' (Agendada para {regra.horario_disparo})")
                executar_regra_especifica(regra)

def executar_regra_especifica(regra):
    # Data limite: Hoje - Dias configurados
    data_corte = datetime.utcnow() - timedelta(days=regra.dias_ausente)
    
    # Busca Pacientes elegíveis
    pacientes_candidatos = Patient.query.filter(
        Patient.clinic_id == regra.clinic_id,
        Patient.last_visit < data_corte,
        Patient.status == 'ativo',
        Patient.receive_marketing == True 
    ).all()

    for paciente in pacientes_candidatos:
        try:
            # 1. Verifica se já tem consulta futura
            tem_agendamento = Appointment.query.filter(
                Appointment.clinic_id == regra.clinic_id,
                Appointment.patient_id == paciente.id,
                Appointment.date_time > datetime.utcnow(),
                Appointment.status != 'cancelled'
            ).first()

            if tem_agendamento:
                continue 

            # 2. Verifica se já está no CRM (Card Aberto)
            card_aberto = CRMCard.query.filter(
                CRMCard.clinic_id == regra.clinic_id,
                CRMCard.paciente_id == paciente.id,
                CRMCard.status == 'open'
            ).first()

            if card_aberto:
                continue 

            # 3. Envia Mensagem
            msg_final = regra.mensagem_template.replace("{nome}", paciente.name) if regra.mensagem_template else f"Olá {paciente.name}!"
            sucesso, log_msg = enviar_whatsapp_interno(regra.clinic_id, paciente.phone, msg_final)

            if sucesso:
                logger.info(f"✅ Recall enviado para {paciente.name}")
                
                # Cria Card no CRM
                estagio_inicial = CRMStage.query.filter_by(clinic_id=regra.clinic_id, is_initial=True).first()
                if not estagio_inicial:
                    estagio_inicial = CRMStage.query.filter_by(clinic_id=regra.clinic_id).order_by(CRMStage.ordem).first()

                if estagio_inicial:
                    novo_card = CRMCard(
                        clinic_id=regra.clinic_id,
                        paciente_id=paciente.id,
                        stage_id=estagio_inicial.id,
                        ultima_interacao=datetime.utcnow(),
                        status='open'
                    )
                    db.session.add(novo_card)
                    db.session.flush()

                    hist = CRMHistory(
                        card_id=novo_card.id,
                        tipo="BOT_RECALL",
                        descricao=f"Robô enviou: {msg_final}"
                    )
                    db.session.add(hist)
                    db.session.commit()
            else:
                logger.error(f"❌ Falha ao enviar para {paciente.name}: {log_msg}")

        except Exception as e:
            logger.error(f"Erro ao processar paciente {paciente.id}: {e}")
            db.session.rollback()

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Roda a cada 60 minutos
    scheduler.add_job(processar_automacoes, 'interval', minutes=60)
    scheduler.start()