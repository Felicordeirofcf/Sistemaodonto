from flask import Blueprint, request, jsonify
from app.models import db, Clinic, CRMStage, CRMCard, Lead, WhatsAppConnection
import logging
import datetime

# Configuração de Logs
logger = logging.getLogger(__name__)

bp = Blueprint('marketing_webhook', __name__)

# Palavras que ATIVAM o robô (para ele não responder seus amigos falando "e ai")
GATILHOS_BOT = [
    "olá", "ola", "oi", "bom dia", "boa tarde", "boa noite", 
    "tudo bem", "agendar", "marcar", "consulta", "preço", 
    "valor", "doutor", "dentista", "endereço", "avaliac", "avaliaç"
]

@bp.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    data = request.get_json()
    
    # 1. Validação Básica
    if not data or 'data' not in data:
        return jsonify({"status": "ignored", "reason": "no data"}), 200

    payload = data['data']
    
    # 2. Verifica se é mensagem de texto recebida
    if 'key' not in payload or payload['key'].get('fromMe') == True:
        return jsonify({"status": "ignored", "reason": "from_me"}), 200

    # 3. Extrai dados vitais
    remote_jid = payload['key'].get('remoteJid') # numero@s.whatsapp.net
    phone = remote_jid.split('@')[0]
    push_name = payload.get('pushName', 'Paciente')
    
    # Pega o texto da mensagem (tenta vários campos possíveis da API)
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

    # 4. Descobre a Clínica dona dessa instância
    instance_owner = data.get('instance') # Nome da instância na Evolution
    # Tenta achar conexão pelo nome da instância ou pelo número dono
    conn = None
    
    # Busca simples: A primeira clínica que tiver conectada (para MVP)
    # Num sistema real, buscaria pelo instance_name exato
    conn = WhatsAppConnection.query.filter_by(status='connected').first()
    
    if not conn:
        print("⚠️ Nenhuma clínica conectada encontrada para processar mensagem.")
        return jsonify({"status": "error", "reason": "no clinic connected"}), 200

    clinic_id = conn.clinic_id

    # 5. Lógica do Robô (Fluxo Simples)
    # Verifica se já existe um card ABERTO para esse telefone
    existing_card = CRMCard.query.join(CRMStage).filter(
        CRMStage.clinic_id == clinic_id,
        CRMCard.paciente_phone == phone,
        CRMStage.is_success == False # Apenas cards em andamento
    ).first()

    # --- CENÁRIO A: JÁ ESTÁ NO CRM (Não faz nada ou avisa humano) ---
    if existing_card:
        print(f"🔄 Paciente {phone} já está no funil. Robô silenciado.")
        return jsonify({"status": "ignored", "reason": "already in crm"}), 200

    # --- CENÁRIO B: NOVO LEAD (Inicia Atendimento) ---
    
    # Filtro: Só ativa se tiver palavra chave (Evita responder amigos)
    eh_gatilho = any(palavra in message_text for palavra in GATILHOS_BOT)
    
    if eh_gatilho:
        print(f"🤖 Robô Ativado para: {phone} | Msg: {message_text}")
        
        # 1. Cria o Card na Coluna "Novo Lead" (Busca Dinâmica)
        stage = CRMStage.query.filter_by(clinic_id=clinic_id, is_initial=True).first()
        
        # Se não achou a marcada como inicial, pega a primeira que tiver
        if not stage:
            stage = CRMStage.query.filter_by(clinic_id=clinic_id).order_by(CRMStage.ordem).first()
            
        if stage:
            try:
                # Salva no Banco
                novo_card = CRMCard(
                    stage_id=stage.id,
                    paciente_nome=push_name, # Salva o nome do WhatsApp (ex: Jesus is King)
                    paciente_phone=phone,
                    historico_conversas=f"Iniciou via WhatsApp: {message_text}",
                    valor_proposta=0
                )
                db.session.add(novo_card)
                db.session.commit()
                print(f"✅ Lead Salvo no CRM! ID: {novo_card.id}")

                # 2. Manda a Resposta Automática (via Evolution API)
                # Você precisaria implementar o envio de volta aqui ou usar a função de envio existente
                # Como este código é o webhook, ele apenas processa a entrada.
                # O envio da resposta "Olá, vi seu contato..." idealmente é feito aqui chamando a API.
                
                # EXEMPLO DE RESPOSTA AUTOMÁTICA (Descomente se tiver a função send_message pronta)
                # from app.utils.whatsapp import send_whatsapp_message
                # send_whatsapp_message(phone, "Olá! 👋 Vi seu contato. Sou o assistente virtual da clínica. Como posso ajudar?", conn.instance_name)

            except Exception as e:
                print(f"❌ Erro ao salvar no CRM: {e}")
                db.session.rollback()
        else:
            print("❌ Nenhuma etapa de CRM configurada para esta clínica.")

    return jsonify({"status": "processed"}), 200