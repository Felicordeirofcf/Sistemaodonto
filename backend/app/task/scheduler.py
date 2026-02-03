import os
import requests
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import and_

# Importa o app e o banco para ter contexto
from app import create_app, db
from app.models import (
    AutomacaoRecall, Patient, Appointment, 
    CRMCard, CRMStage, CRMHistory, WhatsAppConnection
)

# Configuração de Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Scheduler")

# Configurações da API Evolution (Pegando do ambiente)
EVOLUTION_API_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "minha-senha-secreta")

def get_headers():
    return {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json"
    }

# ==============================================================================
# FUNÇÃO 1: O MOTOR DE ENVIO (WhatsApp Interno)
# ==============================================================================
def enviar_whatsapp_interno(clinic_id, telefone, mensagem):
    """
    Função auxiliar para enviar mensagem sem depender da rota Flask (request context).
    Usa a instância dinâmica 'clinica_v3_{id}'
    """
    instance_name = f"clinica_v3_{clinic_id}"
    
    # Limpa o telefone (apenas números)
    phone_number = ''.join(filter(str.isdigit, telefone))
    
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

# ==============================================================================
# FUNÇÃO 2: A LÓGICA DE NEGÓCIO (Recall e CRM)
# ==============================================================================
def processar_automacoes():
    """
    Roda a cada 1 hora. Verifica se existe alguma automação configurada para agora.
    """
    app = create_app()
    with app.app_context():
        # 1. Pega a hora atual (Ex: "09:00", "14:00")
        hora_atual = datetime.now().strftime("%H:00") 
        logger.info(f"⏰ Scheduler rodando: Verificando regras para {hora_atual}...")

        # 2. Busca automações ativas agendadas para esta hora
        # Nota: Ajustamos para buscar horário exato ou aproximado se necessário
        regras = AutomacaoRecall.query.filter_by(ativo=True).all()

        count_envios = 0

        for regra in regras:
            # Verifica se o horário bate (filtro simples python para garantir formato)
            # Se no banco estiver "09:00" e agora for "09:00", ele entra.
            if regra.horario_disparo and regra.horario_disparo.startswith(hora_atual[:2]):
                
                logger.info(f"🚀 Executando regra '{regra.nome}' da Clínica {regra.clinic_id}")
                executar_regra_especifica(regra)

def executar_regra_especifica(regra):
    # Data limite: Hoje - Dias configurados (Ex: Hoje - 180 dias)
    data_corte = datetime.utcnow() - timedelta(days=regra.dias_ausente)
    
    # 1. Buscar Pacientes que sumiram (última visita antes da data de corte)
    pacientes_candidatos = Patient.query.filter(
        Patient.clinic_id == regra.clinic_id,
        Patient.last_visit < data_corte,
        Patient.status == 'ativo'  # Não manda para inativos
    ).all()

    for paciente in pacientes_candidatos:
        try:
            # --- FILTRO 1: SEGURANÇA (Já tem consulta marcada?) ---
            tem_agendamento = Appointment.query.filter(
                Appointment.clinic_id == regra.clinic_id,
                Appointment.patient_id == paciente.id,
                Appointment.date_time > datetime.utcnow(), # Futuro
                Appointment.status != 'cancelled'
            ).first()

            if tem_agendamento:
                continue # Pula, não vamos incomodar quem já marcou.

            # --- FILTRO 2: CRM (Já está sendo trabalhado?) ---
            # Verifica se existe um card ABERTO (não ganho nem perdido)
            card_aberto = CRMCard.query.filter(
                CRMCard.clinic_id == regra.clinic_id,
                CRMCard.paciente_id == paciente.id,
                CRMCard.status == 'open'
            ).first()

            if card_aberto:
                continue # Pula, já estamos conversando com ele.

            # === AÇÃO: DISPARAR RECALL ===
            
            # 1. Prepara a mensagem
            if not regra.mensagem_template:
                msg_final = f"Olá {paciente.name}, faz tempo que não te vemos! Vamos agendar um checkup?"
            else:
                msg_final = regra.mensagem_template.replace("{nome}", paciente.name)

            # 2. Envia WhatsApp
            sucesso, log_msg = enviar_whatsapp_interno(regra.clinic_id, paciente.phone, msg_final)

            if sucesso:
                logger.info(f"✅ Recall enviado para {paciente.name}")
                
                # 3. CRIA CARD NO CRM (KANBAN)
                # Busca a coluna inicial (Ex: "A Contactar")
                estagio_inicial = CRMStage.query.filter_by(
                    clinic_id=regra.clinic_id, 
                    is_initial=True
                ).first()

                # Se não tiver estágio configurado, pega o primeiro que achar ou cria um dummy (segurança)
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
                    db.session.flush() # Para gerar o ID do card

                    # 4. REGISTRA HISTÓRICO
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
            db.session.rollback() # Garante que não trava o loop

# ==============================================================================
# INICIALIZADOR
# ==============================================================================
def start_scheduler():
    scheduler = BackgroundScheduler()
    
    # Adiciona o Job para rodar a cada 1 hora (ou use cron para horários fixos)
    # Ex: minutes=30 roda a cada 30 min. 'hours=1' roda de hora em hora.
    scheduler.add_job(processar_automacoes, 'interval', minutes=60)
    
    # Opcional: Rodar uma vez assim que ligar para teste (comente em produção)
    # scheduler.add_job(processar_automacoes, 'date', run_date=datetime.now() + timedelta(seconds=10))

    scheduler.start()
    logger.info("🚀 Scheduler de Recall Iniciado com Sucesso!")