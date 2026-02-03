from flask import Blueprint, request, jsonify
from app.models import db, Lead, Campaign, Patient, LeadStatus, LeadEvent, WhatsAppConnection
from datetime import datetime
import re
import requests
import os

bp = Blueprint('marketing_webhook', __name__)

# Configuração Rápida (Idealmente viria do banco/env)
EVOLUTION_API_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "minha-senha-secreta")

def send_whatsapp_text(instance, phone, text):
    """Envia mensagem de texto simples via Evolution API"""
    url = f"{EVOLUTION_API_URL}/message/sendText/{instance}"
    headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}
    payload = {"number": phone, "text": text}
    try:
        requests.post(url, json=payload, headers=headers, timeout=5)
    except Exception as e:
        print(f"Erro ao enviar WA: {e}")

@bp.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_inbound():
    data = request.get_json()
    
    # 1. Validação Básica da Evolution API
    if not data or 'data' not in data:
        return jsonify({"status": "ignored"}), 200
        
    payload = data['data']
    key = payload.get('key', {})
    remote_jid = key.get('remoteJid') # Ex: 5511999999999@s.whatsapp.net
    from_me = key.get('fromMe', False)
    
    # Ignora mensagens enviadas por mim ou grupos/status
    if not remote_jid or from_me or 'status@broadcast' in remote_jid or 'g.us' in remote_jid:
        return jsonify({"status": "ignored"}), 200

    # Extrai telefone e Instância
    phone = remote_jid.split('@')[0]
    instance = data.get('instance', 'clinica_v3_1') # Nome da instância que recebeu
    
    # Extrai Texto da Mensagem
    msg_content = payload.get('message', {})
    text = msg_content.get('conversation') or msg_content.get('extendedTextMessage', {}).get('text')
    
    if not text:
        return jsonify({"status": "no_text"}), 200

    # 2. Verifica se é PACIENTE JÁ CADASTRADO (Se for, ignora o marketing)
    # Assumindo clinic_id=1 para MVP. Em produção, buscar clinic_id pela instância.
    clinic_id = 1 
    patient = Patient.query.filter_by(phone=phone, clinic_id=clinic_id).first()
    
    if patient:
        # É paciente antigo -> Deixa o fluxo normal de atendimento (não interfere)
        return jsonify({"status": "existing_patient"}), 200

    # 3. Verifica se é LEAD (Se não existe, cria)
    lead = Lead.query.filter_by(phone=phone, clinic_id=clinic_id).first()
    
    if not lead:
        # É um NOVO LEAD! Vamos ver se veio de campanha.
        campaign_id = None
        
        # Procura token [ref:XXXX] na mensagem
        match = re.search(r'\[ref:(.*?)\]', text)
        if match:
            code = match.group(1)
            camp = Campaign.query.filter_by(tracking_code=code, clinic_id=clinic_id).first()
            if camp:
                campaign_id = camp.id
                camp.leads_count += 1 # Incrementa métrica da campanha
        
        lead = Lead(
            clinic_id=clinic_id,
            phone=phone,
            campaign_id=campaign_id,
            source='whatsapp_inbound',
            status=LeadStatus.IN_CHAT,
            chatbot_state='START',
            name=payload.get('pushName') # Tenta pegar o nome do perfil do WA
        )
        db.session.add(lead)
        db.session.commit()
        
        # Log do evento
        db.session.add(LeadEvent(lead_id=lead.id, event_type='lead_created', metadata_json={'text': text}))
        db.session.commit()

    # 4. MÁQUINA DE ESTADOS DO CHATBOT (Qualificação)
    process_chatbot(lead, text, instance)
    
    return jsonify({"status": "processed"}), 200

def process_chatbot(lead, text, instance):
    """Lógica simples de perguntas e respostas"""
    
    # Se o lead já foi qualificado ou convertido, o bot para de responder
    if lead.status in [LeadStatus.QUALIFIED, LeadStatus.SCHEDULED, LeadStatus.CONVERTED]:
        return

    state = lead.chatbot_state
    
    if state == 'START':
        # Primeiro contato
        msg = f"Olá! 👋 Vi que você entrou em contato com a nossa clínica.\nEu sou o assistente virtual. Para começarmos, você poderia me confirmar seu *nome completo*?"
        send_whatsapp_text(instance, lead.phone, msg)
        
        lead.chatbot_state = 'ASK_INTEREST' # Avança estado
        
    elif state == 'ASK_INTEREST':
        # Usuário respondeu o nome (teoricamente)
        # Salva o nome se não tiver
        if not lead.name or lead.name == lead.phone:
            lead.name = text.strip()
            
        msg = f"Prazer, {lead.name}! 😄\n\nQual tratamento você está procurando hoje?\n1. Implante\n2. Clareamento\n3. Aparelho\n4. Dor/Emergência\n5. Outros"
        send_whatsapp_text(instance, lead.phone, msg)
        
        lead.chatbot_state = 'HANDOFF' # Próximo passo encerra
        
    elif state == 'HANDOFF':
        # Usuário respondeu o interesse
        lead.chatbot_data = {"interest": text.strip()}
        
        msg = "Perfeito! Já anotei aqui. 📝\n\nUm de nossos atendentes humanos vai falar com você em instantes para agendar sua avaliação. Obrigado!"
        send_whatsapp_text(instance, lead.phone, msg)
        
        # Finaliza o bot
        lead.status = LeadStatus.QUALIFIED
        lead.chatbot_state = 'DONE'
    
    lead.updated_at = datetime.utcnow()
    db.session.commit()