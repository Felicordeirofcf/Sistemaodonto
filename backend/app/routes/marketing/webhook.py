from flask import Blueprint, request, jsonify
from app.models import db, Clinic, CRMStage, CRMCard, Lead, WhatsAppConnection
import logging
import requests
import os

logger = logging.getLogger(__name__)

bp = Blueprint('marketing_webhook', __name__)

# Configurações da API
EVOLUTION_API_URL = os.getenv("WHATSAPP_QR_SERVICE_URL", "http://localhost:8080").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")

# Palavras que ATIVAM o robô
GATILHOS_BOT = [
    "olá", "ola", "oi", "bom dia", "boa tarde", "boa noite", 
    "tudo bem", "agendar", "marcar", "consulta", "preço", 
    "valor", "doutor", "dentista", "endereço", "avaliac", "avaliaç"
]

@bp.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    data = request.get_json()
    
    if not data or 'data' not in data:
        return jsonify({"status": "ignored", "reason": "no data"}), 200

    payload = data['data']
    
    # Verifica se é mensagem enviada por mim (ignora)
    if 'key' not in payload or payload['key'].get('fromMe') == True:
        return jsonify({"status": "ignored", "reason": "from_me"}), 200

    # Dados da Mensagem
    remote_jid = payload['key'].get('remoteJid') 
    phone = remote_jid.split('@')[0]
    push_name = payload.get('pushName', 'Paciente')
    
    # Extrai texto
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

    # --- CORREÇÃO DO ERRO "NENHUMA CLÍNICA CONECTADA" ---
    # Tenta achar conexão no banco
    conn = WhatsAppConnection.query.filter_by(status='connected').first()
    
    # Se não achou no banco, força busca na API (Auto-Recovery)
    if not conn:
        print("⚠️ Conexão não encontrada no DB. Buscando na API...")
        try:
            url = f"{EVOLUTION_API_URL}/instance/fetchInstances"
            headers = {"apikey": EVOLUTION_API_KEY}
            resp = requests.get(url, headers=headers, timeout=5)
            
            if resp.status_code == 200:
                instances = resp.json()
                # Pega a primeira instância ONLINE
                active_instance = next((i for i in instances if i.get('instance', {}).get('status') == 'open'), None)
                
                if active_instance:
                    owner_jid = active_instance['instance']['owner']
                    instance_name = active_instance['instance']['instanceName']
                    
                    # Salva/Cria no banco agora mesmo
                    conn = WhatsAppConnection.query.filter_by(instance_name=instance_name).first()
                    if not conn:
                        conn = WhatsAppConnection(
                            clinic_id=1, # Assume clínica 1 para recuperação
                            instance_name=instance_name,
                            status='connected',
                            session_data={"me": {"id": owner_jid}}
                        )
                        db.session.add(conn)
                    else:
                        conn.status = 'connected'
                        conn.session_data = {"me": {"id": owner_jid}}
                    
                    db.session.commit()
                    print(f"✅ Conexão recuperada e salva: {instance_name}")
        except Exception as e:
            print(f"❌ Erro ao tentar recuperar conexão: {e}")

    if not conn:
        print("❌ FALHA FATAL: Nenhuma clínica conectada encontrada.")
        return jsonify({"status": "error", "reason": "no clinic connected"}), 200

    clinic_id = conn.clinic_id

    # --- LÓGICA DE CRM ---
    existing_card = CRMCard.query.join(CRMStage).filter(
        CRMStage.clinic_id == clinic_id,
        CRMCard.paciente_phone == phone,
        CRMStage.is_success == False
    ).first()

    if existing_card:
        print(f"🔄 Paciente {phone} já no funil.")
        return jsonify({"status": "ignored", "reason": "already in crm"}), 200

    # Filtro de Gatilho
    eh_gatilho = any(palavra in message_text for palavra in GATILHOS_BOT)
    
    if eh_gatilho:
        print(f"🤖 Novo Lead Detectado: {phone}")
        
        # Busca coluna inicial de forma segura
        stage = CRMStage.query.filter_by(clinic_id=clinic_id, is_initial=True).first()
        if not stage:
            stage = CRMStage.query.filter_by(clinic_id=clinic_id).order_by(CRMStage.ordem).first()
            
        if stage:
            try:
                novo_card = CRMCard(
                    stage_id=stage.id,
                    paciente_nome=push_name,
                    paciente_phone=phone,
                    historico_conversas=f"WhatsApp: {message_text}",
                    valor_proposta=0
                )
                db.session.add(novo_card)
                db.session.commit()
                print(f"✅ Card criado no CRM (ID: {novo_card.id})")
            except Exception as e:
                print(f"❌ Erro DB: {e}")
                db.session.rollback()

    return jsonify({"status": "processed"}), 200