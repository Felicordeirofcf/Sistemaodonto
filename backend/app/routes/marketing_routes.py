from flask import Blueprint, jsonify, request
from app.models import db, Lead, User, Patient, Appointment, MarketingCampaign, Clinic
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import requests
import os

marketing_bp = Blueprint('marketing', __name__)

# --- 1. GESTÃO DE LEADS (MANTIDO IGUAL) ---

@marketing_bp.route('/marketing/leads', methods=['GET'])
@jwt_required()
def get_leads():
    try:
        user = User.query.get(get_jwt_identity())
        leads = Lead.query.filter_by(clinic_id=user.clinic_id).all()
        return jsonify([lead.to_dict() for lead in leads]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@marketing_bp.route('/marketing/leads', methods=['POST'])
@jwt_required()
def create_lead():
    try:
        user = User.query.get(get_jwt_identity())
        data = request.get_json()
        new_lead = Lead(
            clinic_id=user.clinic_id,
            name=data.get('name'),
            phone=data.get('phone'),
            source=data.get('source', 'Manual'),
            status='new',
            notes=data.get('notes', '')
        )
        db.session.add(new_lead)
        db.session.commit()
        return jsonify(new_lead.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro ao criar lead'}), 500

@marketing_bp.route('/marketing/leads/<int:id>/move', methods=['PUT'])
@jwt_required()
def move_lead(id):
    user = User.query.get(get_jwt_identity())
    data = request.get_json()
    lead = Lead.query.filter_by(id=id, clinic_id=user.clinic_id).first()
    if not lead: return jsonify({'error': 'Lead não encontrado'}), 404
    lead.status = data.get('status')
    db.session.commit()
    return jsonify({'message': 'Lead movido com sucesso!'}), 200


# --- 2. INTEGRAÇÃO REAL COM META ADS (CORRIGIDA PARA AUTO-DESCOBERTA) ---

@marketing_bp.route('/marketing/meta/connect', methods=['POST'])
@jwt_required()
def connect_meta_real():
    """
    Recebe o token, troca por Long-Lived e DESCOBRE o ID da conta de anúncios automaticamente.
    """
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)
        data = request.get_json()
        
        short_lived_token = data.get('accessToken')
        
        if not short_lived_token:
            return jsonify({'error': 'Token de acesso não fornecido'}), 400

        # 1. Troca por Token de Longa Duração
        app_id = os.environ.get('META_APP_ID')
        app_secret = os.environ.get('META_APP_SECRET')
        long_lived_token = short_lived_token

        if app_id and app_secret:
            url = "https://graph.facebook.com/v19.0/oauth/access_token"
            params = {
                'grant_type': 'fb_exchange_token',
                'client_id': app_id,
                'client_secret': app_secret,
                'fb_exchange_token': short_lived_token
            }
            resp = requests.get(url, params=params)
            if resp.status_code == 200:
                long_lived_token = resp.json().get('access_token')

        # 2. AUTO-DESCOBERTA DO ID DA CONTA DE ANÚNCIOS (O Pulo do Gato)
        # Se o front não mandou o ID, vamos perguntar pro Facebook quais contas o usuário tem
        ad_account_id = data.get('adAccountId')
        
        if not ad_account_id:
            try:
                me_url = "https://graph.facebook.com/v19.0/me/adaccounts"
                me_params = {
                    'access_token': long_lived_token,
                    'fields': 'account_id,name'
                }
                me_resp = requests.get(me_url, params=me_params)
                
                if me_resp.status_code == 200:
                    accounts_data = me_resp.json().get('data', [])
                    if accounts_data:
                        # Pega a primeira conta de anúncios encontrada
                        ad_account_id = accounts_data[0].get('account_id')
                        print(f"Conta de Anúncios encontrada: {ad_account_id}")
            except Exception as e:
                print(f"Erro ao buscar ad accounts: {e}")

        # 3. Salva na Clínica
        clinic.meta_access_token = long_lived_token
        if ad_account_id:
            # Garante que salva só o número ou com act_ se preferir, aqui salvamos limpo
            clinic.meta_ad_account_id = str(ad_account_id).replace('act_', '')
            
        clinic.last_sync_at = datetime.utcnow()
        db.session.commit()

        if not ad_account_id:
            return jsonify({'message': 'Facebook conectado, mas nenhuma conta de anúncios foi encontrada. Crie uma no Gerenciador de Anúncios.', 'token_type': 'long-lived'}), 200

        return jsonify({'message': 'Conexão com Meta Ads estabelecida!', 'ad_account_id': ad_account_id}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@marketing_bp.route('/marketing/meta/sync', methods=['POST'])
@jwt_required()
def sync_meta_real():
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        # Verificação robusta
        if not clinic.meta_access_token:
            return jsonify({'error': 'Token não encontrado. Faça login novamente.'}), 400
            
        if not clinic.meta_ad_account_id:
            # Tenta recuperar o ID de novo se tiver token mas não tiver ID
            return jsonify({'error': 'ID da conta de anúncios não configurado. Refaça a conexão.'}), 400

        # 1. Configura a chamada para a Graph API
        ad_account_id = clinic.meta_ad_account_id
        url = f"https://graph.facebook.com/v19.0/act_{ad_account_id}/insights"
        
        params = {
            'access_token': clinic.meta_access_token,
            'date_preset': 'maximum',
            'fields': 'spend,clicks,cpc,cpm,impressions,actions',
            'level': 'account'
        }

        response = requests.get(url, params=params)
        
        # Tratamento de erro específico do Token Expirado
        if response.status_code == 401:
             return jsonify({'error': 'Token expirado ou inválido do Facebook'}), 401

        if response.status_code != 200:
            error_data = response.json()
            return jsonify({'error': 'Erro no Facebook API', 'details': error_data}), 400

        data = response.json().get('data', [])
        
        # Se não tiver dados (conta nova sem gastos), retornamos zeros em vez de erro
        spend = 0.0
        clicks = 0
        cpc = 0.0

        if data:
            stats = data[0]
            spend = float(stats.get('spend', 0.0))
            clicks = int(stats.get('clicks', 0))
            cpc = float(stats.get('cpc', 0.0))
        
        # Atualiza banco
        clinic.current_ad_balance = spend
        clinic.last_sync_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': 'Sincronização Real Finalizada',
            'spend': spend,
            'clicks': clicks,
            'cpc': cpc
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f"Erro interno: {str(e)}"}), 500


# --- 3. REATIVAÇÃO (MANTIDO IGUAL) ---

@marketing_bp.route('/marketing/campaign/recall', methods=['GET'])
@jwt_required()
def get_recall_campaign():
    try:
        user = User.query.get(get_jwt_identity())
        six_months_ago = datetime.utcnow() - timedelta(days=180)
        
        candidates = Patient.query.filter(
            Patient.clinic_id == user.clinic_id,
            Patient.last_visit <= six_months_ago
        ).all()

        amanha = datetime.utcnow().date() + timedelta(days=1)
        agendamentos_amanha = Appointment.query.filter(
            Appointment.clinic_id == user.clinic_id,
            db.func.date(Appointment.date_time) == amanha
        ).count()
        
        has_slots = agendamentos_amanha < 8 
        output = []
        for p in candidates:
            last_visit_str = p.last_visit.strftime('%d/%m/%Y') if p.last_visit else "Não registrada"
            msg = f"Olá {p.name}! O Dr. notou que sua última revisão foi em {last_visit_str}. "
            msg += "Temos horários livres para amanhã, vamos agendar?" if has_slots else "Que tal agendar sua limpeza preventiva?"

            output.append({
                'id': p.id,
                'name': p.name,
                'phone': p.phone,
                'last_visit': last_visit_str,
                'suggested_msg': msg
            })
        
        return jsonify(output), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 4. ROTA DE CRESCIMENTO (MANTER PARA NÃO QUEBRAR O FRONT) ---
@marketing_bp.route('/marketing/campaign/activate', methods=['POST'])
@jwt_required()
def activate_ads():
    # Rota mantida para compatibilidade, mas o foco agora é o /connect e /sync
    return jsonify({'message': 'Use a conexão real com Meta Ads acima'}), 200