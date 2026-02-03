from flask import Blueprint, request, jsonify
from app.models import db, Clinic, CRMStage, CRMCard, Lead, WhatsAppConnection
import logging
import requests
import os

logger = logging.getLogger(__name__)

bp = Blueprint('marketing_webhook', __name__)

# Configurações da API Evolution
EVOLUTION_API_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")

# Palavras que ATIVAM o robô
GATILHOS_BOT = [
    "olá", "ola", "oi", "bom dia", "boa tarde", "boa noite", 
    "tudo bem", "agendar", "marcar", "consulta", "preço", 
    "valor", "doutor", "dentista", "endereço", "avaliac", "avaliaç"
]

def garantir_etapas_crm(clinic_id):
    """Garante que o funil completo exista (SaaS Ready)"""
    etapas_padrao = [
        {"nome": "Novo Lead", "cor": "#3b82f6", "is_initial": True},
        {"nome": "Contactado", "cor": "#f59e0b", "is_initial": False},
        {"nome": "Agendado", "cor": "#10b981", "is_initial": False},
        {"nome": "Avaliado", "cor": "#8b5cf6", "is_initial": False},
        {"nome": "Perdido", "cor": "#ef4444", "is_initial": False}
    ]
    
    exists = CRMStage.query.filter_by(clinic_id=clinic_id).first()
    if not exists:
        logger.info(f"🛠️ Criando etapas padrão do CRM para clínica {clinic_id}")
        for i, etapa in enumerate(etapas_padrao):
            nova_etapa = CRMStage(
                clinic_id=clinic_id,
                nome=etapa["nome"],
                cor=etapa["cor"],
                ordem=i,
                is_initial=etapa["is_initial"],
                is_success=(etapa["nome"] == "Agendado")
            )
            db.session.add(nova_etapa)
        db.session.commit()

@bp.route('/webhook/whatsapp', methods=['POST'])
@bp.route('/webhook/whatsapp/messages-upsert', methods=['POST'])
def whatsapp_webhook():
    data = request.get_json()
    
    if not data or 'data' not in data:
        return jsonify({"status": "ignored", "reason": "no data"}), 200

    payload = data['data']
    
    # 1. Ignora mensagens enviadas pela própria clínica
    if 'key' not in payload or payload['key'].get('fromMe') == True:
        return jsonify({"status": "ignored", "reason": "from_me"}), 200

    # 2. Extração de dados
    remote_jid = payload['key'].get('remoteJid') 
    phone = remote_jid.split('@')[0]
    push_name = payload.get('pushName', 'Paciente')
    
    message_text = ""
    if 'message' in payload:
        msg = payload['message']
        if 'conversation' in msg:
            message_text = msg['conversation']
        elif 'extendedTextMessage' in msg:
            message_text = msg['extendedTextMessage'].get('text', '')
    
    message_text = message_text.lower().strip()
    if not message_text:
        return jsonify({"status": "ignored", "reason": "no text"}), 200

    # 3. IDENTIFICAÇÃO DA CLÍNICA (LÓGICA DE ÂNCORA)
    # Identifica qual número de WhatsApp recebeu a mensagem
    instance_owner = data.get('instance', {}).get('owner', '')
    owner_phone = instance_owner.split('@')[0].split(':')[0]

    # Busca a clínica dona deste número no cadastro fixo
    clinic = Clinic.query.filter_by(whatsapp_number=owner_phone).first()
    
    # Fallback para Clínica 1 se o número não estiver vinculado
    clinic_id = clinic.id if clinic else 1

    # 4. Garante infraestrutura do CRM
    garantir_etapas_crm(clinic_id)

    # 5. Evita duplicidade (não cria novo card se já houver um aberto)
    existing_card = CRMCard.query.filter(
        CRMCard.clinic_id == clinic_id,
        CRMCard.paciente_phone == phone,
        CRMCard.status == 'open'
    ).first()

    if existing_card:
        return jsonify({"status": "ignored", "reason": "already in crm"}), 200

    # 6. Filtro de Gatilho e Criação de Card
    eh_gatilho = any(palavra in message_text for palavra in GATILHOS_BOT)
    
    if eh_gatilho:
        # Localiza a etapa inicial do funil
        stage = CRMStage.query.filter_by(clinic_id=clinic_id, is_initial=True).first()
            
        if stage:
            try:
                novo_card = CRMCard(
                    clinic_id=clinic_id,
                    stage_id=stage.id,
                    paciente_nome=push_name,
                    paciente_phone=phone,
                    historico_conversas=f"WhatsApp: {message_text}",
                    valor_proposta=0,
                    status='open'
                )
                db.session.add(novo_card)
                db.session.commit()
                logger.info(f"✅ Lead '{push_name}' adicionado ao Funil de Recuperação da Clínica {clinic_id}.")
            except Exception as e:
                logger.error(f"❌ Erro ao salvar Lead: {e}")
                db.session.rollback()

    return jsonify({"status": "processed"}), 200