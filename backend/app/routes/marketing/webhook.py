from flask import Blueprint, request, jsonify
from app.models import db, Clinic, CRMStage, CRMCard, Lead, Campaign, LeadEvent
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

bp = Blueprint('marketing_webhook', __name__)

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
    
    message_text_lower = message_text.lower().strip()
    if not message_text_lower:
        return jsonify({"status": "ignored", "reason": "no text"}), 200

    # 3. IDENTIFICAÇÃO DA CLÍNICA (LÓGICA DE ÂNCORA)
    # Identifica qual número de WhatsApp recebeu a mensagem
    instance_owner = data.get('instance', {}).get('owner', '')
    owner_phone = instance_owner.split('@')[0].split(':')[0]

    # Busca a clínica dona deste número no cadastro fixo
    clinic = Clinic.query.filter_by(whatsapp_number=owner_phone).first()
    clinic_id = clinic.id if clinic else 1

    # 4. DETECÇÃO DE CAMPANHA (tracking_code)
    campaign = None
    if "[ref:" in message_text:
        try:
            # Extrai o código entre [ref: e ]
            code = message_text.split("[ref:")[1].split("]")[0]
            campaign = Campaign.query.filter_by(tracking_code=code).first()
        except Exception as e:
            logger.warning(f"⚠️ Falha ao extrair tracking_code: {e}")

    # 5. CONVERSÃO AUTOMÁTICA EM LEAD
    if campaign:
        # Garante infraestrutura do CRM
        garantir_etapas_crm(clinic_id)

        # Verifica se já existe um lead ou card aberto para este telefone
        existing_card = CRMCard.query.filter(
            CRMCard.clinic_id == clinic_id,
            CRMCard.paciente_phone == phone,
            CRMCard.status == 'open'
        ).first()

        if not existing_card:
            # Localiza a etapa inicial do funil ('Novo Lead')
            stage = CRMStage.query.filter_by(clinic_id=clinic_id, is_initial=True).first()
            
            if stage:
                try:
                    # Cria o Lead na tabela de marketing
                    novo_lead = Lead(
                        clinic_id=clinic_id,
                        campaign_id=campaign.id,
                        name=push_name,
                        phone=phone,
                        source=f"Campanha: {campaign.name}",
                        status='novo'
                    )
                    db.session.add(novo_lead)
                    
                    # Cria o Card no CRM (Organização Visual)
                    novo_card = CRMCard(
                        clinic_id=clinic_id,
                        stage_id=stage.id,
                        paciente_nome=push_name, # pushName do WhatsApp
                        paciente_phone=phone,
                        historico_conversas=f"Lead da Campanha '{campaign.name}': {message_text}",
                        valor_proposta=0,
                        status='open'
                    )
                    db.session.add(novo_card)
                    
                    # Incrementa contador de leads da campanha
                    campaign.leads_count += 1
                    
                    # Registra evento de conversão
                    event = LeadEvent(
                        campaign_id=campaign.id,
                        event_type='msg_in',
                        metadata_json={'phone': phone, 'push_name': push_name, 'message': message_text}
                    )
                    db.session.add(event)
                    
                    db.session.commit()
                    logger.info(f"🚀 Automação Silenciosa: Lead '{push_name}' convertido e adicionado ao CRM da Clínica {clinic_id}.")
                except Exception as e:
                    logger.error(f"❌ Erro na conversão automática: {e}")
                    db.session.rollback()
        else:
            # Se já existe card, apenas registra o evento se for de campanha
            try:
                event = LeadEvent(
                    campaign_id=campaign.id,
                    event_type='msg_in',
                    metadata_json={'phone': phone, 'message': message_text, 'note': 'already_in_crm'}
                )
                db.session.add(event)
                db.session.commit()
            except:
                db.session.rollback()

    return jsonify({"status": "processed"}), 200
