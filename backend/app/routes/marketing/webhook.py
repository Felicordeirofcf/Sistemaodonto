from flask import Blueprint, request, jsonify
from app.models import db, Lead, Campaign, Patient, LeadStatus, LeadEvent
from datetime import datetime
import re
import requests
import os

bp = Blueprint('marketing_webhook', __name__)

# Configuração
EVOLUTION_API_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")

def send_whatsapp_text(instance, phone, text):
    """Envia mensagem de texto via Evolution API"""
    # Ajuste aqui se sua instância tiver outro nome
    if not instance: instance = "clinica_v3_1" 
    
    url = f"{EVOLUTION_API_URL}/message/sendText/{instance}"
    headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}
    payload = {"number": phone, "text": text}
    try:
        print(f"📤 Enviando para {phone}: {text[:30]}...")
        requests.post(url, json=payload, headers=headers, timeout=5)
    except Exception as e:
        print(f"❌ Erro ao enviar WA: {e}")

# ✅ MUDANÇA AQUI: Adicionei 'GET' na lista de methods
@bp.route('/webhook/whatsapp', methods=['POST', 'GET'])
def whatsapp_inbound():
    # 1. Se for acesso via Navegador (GET), retorna sucesso para teste
    if request.method == 'GET':
        return jsonify({
            "status": "online", 
            "message": "O Webhook de Marketing está ativo e aguardando mensagens via POST!"
        }), 200

    # 2. Lógica normal do Webhook (POST)
    data = request.get_json()
    
    if not data or 'data' not in data:
        return jsonify({"status": "ignored"}), 200
        
    payload = data['data']
    key = payload.get('key', {})
    remote_jid = key.get('remoteJid') 
    from_me = key.get('fromMe', False)
    
    # Ignora mensagens próprias ou de grupos
    if not remote_jid or from_me or 'status@broadcast' in remote_jid or 'g.us' in remote_jid:
        return jsonify({"status": "ignored"}), 200

    phone = remote_jid.split('@')[0]
    instance = data.get('instance', 'clinica_v3_1')
    
    msg_content = payload.get('message', {})
    text = msg_content.get('conversation') or msg_content.get('extendedTextMessage', {}).get('text')
    
    if not text:
        return jsonify({"status": "no_text"}), 200

    # Lógica de Identificação (Paciente vs Lead)
    clinic_id = 1 
    
    # Verifica Paciente Existente
    patient = Patient.query.filter_by(phone=phone, clinic_id=clinic_id).first()
    if patient:
        return jsonify({"status": "existing_patient"}), 200

    # Verifica/Cria Lead
    lead = Lead.query.filter_by(phone=phone, clinic_id=clinic_id).first()
    
    if not lead:
        campaign_id = None
        match = re.search(r'\[ref:(.*?)\]', text)
        if match:
            code = match.group(1)
            camp = Campaign.query.filter_by(tracking_code=code, clinic_id=clinic_id).first()
            if camp:
                campaign_id = camp.id
                camp.leads_count += 1
        
        lead = Lead(
            clinic_id=clinic_id,
            phone=phone,
            campaign_id=campaign_id,
            source='whatsapp_inbound',
            status=LeadStatus.IN_CHAT,
            chatbot_state='START',
            name=payload.get('pushName')
        )
        db.session.add(lead)
        db.session.commit()
        
        # Log
        db.session.add(LeadEvent(lead_id=lead.id, event_type='lead_created', metadata_json={'text': text}))
        db.session.commit()

    # Processa Resposta do Robô
    process_chatbot(lead, text, instance)
    
    return jsonify({"status": "processed"}), 200

def process_chatbot(lead, text, instance):
    if lead.status in [LeadStatus.QUALIFIED, LeadStatus.SCHEDULED, LeadStatus.CONVERTED]:
        return

    state = lead.chatbot_state
    
    if state == 'START':
        msg = f"Olá! 👋 Vi que você entrou em contato com a nossa clínica.\nEu sou o assistente virtual. Para começarmos, você poderia me confirmar seu *nome completo*?"
        send_whatsapp_text(instance, lead.phone, msg)
        lead.chatbot_state = 'ASK_INTEREST'
        
    elif state == 'ASK_INTEREST':
        if not lead.name or lead.name == lead.phone:
            lead.name = text.strip()
            
        msg = f"Prazer, {lead.name}! 😄\n\nQual tratamento você está procurando hoje?\n1. Implante\n2. Clareamento\n3. Aparelho\n4. Dor/Emergência\n5. Outros"
        send_whatsapp_text(instance, lead.phone, msg)
        lead.chatbot_state = 'HANDOFF'
        
    elif state == 'HANDOFF':
        lead.chatbot_data = {"interest": text.strip()}
        msg = "Perfeito! Já anotei aqui. 📝\n\nUm de nossos atendentes humanos vai falar com você em instantes para agendar sua avaliação. Obrigado!"
        send_whatsapp_text(instance, lead.phone, msg)
        lead.status = LeadStatus.QUALIFIED
        lead.chatbot_state = 'DONE'
    
    lead.updated_at = datetime.utcnow()
    db.session.commit()