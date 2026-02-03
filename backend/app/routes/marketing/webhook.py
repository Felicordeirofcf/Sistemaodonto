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

# Palavras que ATIVAM o robô (Filtro para evitar responder amigos/contatos pessoais)
GATILHOS_BOT = [
    "olá", "ola", "oi", "bom dia", "boa tarde", "boa noite", 
    "tudo bem", "agendar", "marcar", "consulta", "preço", 
    "valor", "doutor", "dentista", "endereço", "avaliac", "avaliaç"
]

@bp.route('/webhook/whatsapp', methods=['POST'])
@bp.route('/webhook/whatsapp/messages-upsert', methods=['POST'])
def whatsapp_webhook():
    data = request.get_json()
    
    if not data or 'data' not in data:
        return jsonify({"status": "ignored", "reason": "no data"}), 200

    payload = data['data']
    
    # 1. Ignora mensagens enviadas pelo próprio número da clínica
    if 'key' not in payload or payload['key'].get('fromMe') == True:
        return jsonify({"status": "ignored", "reason": "from_me"}), 200

    # 2. Extração de dados do Lead
    remote_jid = payload['key'].get('remoteJid') 
    phone = remote_jid.split('@')[0]
    push_name = payload.get('pushName', 'Paciente')
    
    # Captura o texto da mensagem (suporta diferentes formatos da API)
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

    # 3. Localização da Clínica (Foco em Clínica ID 1 para ambiente único)
    conn = WhatsAppConnection.query.filter_by(status='connected').first()
    
    # Auto-Recovery: Se a conexão sumiu do banco mas a API está ativa, recupera agora
    if not conn:
        logger.info("⚠️ Conexão não encontrada no DB. Tentando recuperar via Evolution API...")
        try:
            url = f"{EVOLUTION_API_URL}/instance/fetchInstances"
            headers = {"apikey": EVOLUTION_API_KEY}
            resp = requests.get(url, headers=headers, timeout=5)
            
            if resp.status_code == 200:
                instances = resp.json()
                # Busca qualquer instância com status 'open' ou 'connected'
                active_instance = next((i for i in instances if i.get('instance', {}).get('status') in ['open', 'connected']), None)
                
                if active_instance:
                    inst_data = active_instance['instance']
                    instance_name = inst_data['instanceName']
                    owner_jid = inst_data.get('owner') or inst_data.get('jid')
                    
                    conn = WhatsAppConnection(
                        clinic_id=1,
                        instance_name=instance_name,
                        status='connected',
                        session_data={"me": {"id": owner_jid}}
                    )
                    db.session.add(conn)
                    db.session.commit()
                    logger.info(f"✅ Conexão recuperada automaticamente: {instance_name}")
        except Exception as e:
            logger.error(f"❌ Falha no Auto-Recovery do Webhook: {e}")

    # Fallback final se nada funcionar
    clinic_id = conn.clinic_id if conn else 1

    # 4. Lógica do CRM (Evita duplicidade de cards abertos)
    existing_card = CRMCard.query.filter(
        CRMCard.clinic_id == clinic_id,
        CRMCard.paciente_phone == phone,
        CRMCard.status == 'open'
    ).first()

    if existing_card:
        logger.info(f"🔄 Lead {phone} já possui um card aberto no CRM.")
        return jsonify({"status": "ignored", "reason": "already in crm"}), 200

    # 5. Filtro de Gatilho e Criação de Card
    eh_gatilho = any(palavra in message_text for palavra in GATILHOS_BOT)
    
    if eh_gatilho:
        logger.info(f"🤖 Novo Lead detectado via WhatsApp: {phone}")
        
        # Localiza a etapa inicial do funil de vendas
        stage = CRMStage.query.filter_by(clinic_id=clinic_id, is_initial=True).first()
        if not stage:
            stage = CRMStage.query.filter_by(clinic_id=clinic_id).order_by(CRMStage.ordem).first()
            
        if stage:
            try:
                novo_card = CRMCard(
                    clinic_id=clinic_id,
                    stage_id=stage.id,
                    paciente_nome=push_name,
                    paciente_phone=phone,
                    historico_conversas=f"Início via WhatsApp: {message_text}",
                    valor_proposta=0,
                    status='open'
                )
                db.session.add(novo_card)
                db.session.commit()
                logger.info(f"✅ Card criado com sucesso no CRM (ID: {novo_card.id})")
            except Exception as e:
                logger.error(f"❌ Erro ao salvar Lead no banco de dados: {e}")
                db.session.rollback()

    return jsonify({"status": "processed"}), 200