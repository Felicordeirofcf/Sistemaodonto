from flask import Blueprint, jsonify, request
from app.models import db, Lead, User, Patient, Appointment, MarketingCampaign, Clinic
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import requests
import os
import random  # Necessário para a simulação da IA

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


# --- 2. INTEGRAÇÃO REAL COM META ADS ---

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

        # 2. AUTO-DESCOBERTA DO ID DA CONTA DE ANÚNCIOS
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
                        ad_account_id = accounts_data[0].get('account_id')
            except Exception as e:
                print(f"Erro ao buscar ad accounts: {e}")

        # 3. Salva na Clínica
        clinic.meta_access_token = long_lived_token
        if ad_account_id:
            clinic.meta_ad_account_id = str(ad_account_id).replace('act_', '')
            
        clinic.last_sync_at = datetime.utcnow()
        db.session.commit()

        if not ad_account_id:
            return jsonify({'message': 'Conectado, mas nenhuma conta de anúncios encontrada.', 'token_type': 'long-lived'}), 200

        return jsonify({'message': 'Conexão com Meta Ads estabelecida!', 'ad_account_id': ad_account_id}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@marketing_bp.route('/marketing/meta/sync', methods=['POST'])
@jwt_required()
def sync_meta_real():
    """
    Sincroniza GASTOS (Insights) e LEADS (Formulários) do Facebook.
    """
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        if not clinic.meta_access_token or not clinic.meta_ad_account_id:
            return jsonify({'error': 'Conta de anúncios não conectada.'}), 400

        ad_account_id = clinic.meta_ad_account_id.replace('act_', '')
        
        # --- PARTE A: SINCRONIZA ESTATÍSTICAS (GASTOS) ---
        url_stats = f"https://graph.facebook.com/v19.0/act_{ad_account_id}/insights"
        params_stats = {
            'access_token': clinic.meta_access_token,
            'date_preset': 'maximum',
            'fields': 'spend,clicks,cpc,impressions',
            'level': 'account'
        }
        
        response = requests.get(url_stats, params=params_stats)
        
        if response.status_code == 401:
             return jsonify({'error': 'Token expirado. Reconecte o Facebook.'}), 401

        stats_data = response.json().get('data', [])
        
        spend = 0.0
        clicks = 0
        cpc = 0.0

        if stats_data:
            stats = stats_data[0]
            spend = float(stats.get('spend', 0.0))
            clicks = int(stats.get('clicks', 0))
            cpc = float(stats.get('cpc', 0.0))
        
        # Atualiza Saldo
        clinic.current_ad_balance = spend
        clinic.last_sync_at = datetime.utcnow()
        
        # Atualiza Campanha de Resumo
        camp = MarketingCampaign.query.filter_by(clinic_id=clinic.id, name="Resumo Meta Ads").first()
        if not camp:
            camp = MarketingCampaign(clinic_id=clinic.id, name="Resumo Meta Ads", status='active')
            db.session.add(camp)
        
        camp.clicks = clicks
        camp.cost_per_click = cpc
        camp.budget = spend
        
        # --- PARTE B: IMPORTAÇÃO AUTOMÁTICA DE LEADS ---
        new_leads_count = 0
        try:
            url_leads = f"https://graph.facebook.com/v19.0/act_{ad_account_id}/ads"
            params_leads = {
                'access_token': clinic.meta_access_token,
                'fields': 'name,leads{created_time,field_data}',
                'limit': 50
            }
            
            resp_leads = requests.get(url_leads, params=params_leads)
            ads_list = resp_leads.json().get('data', [])
            
            for ad in ads_list:
                if 'leads' in ad:
                    fb_leads = ad['leads']['data']
                    for fb_lead in fb_leads:
                        field_data = fb_lead.get('field_data', [])
                        lead_info = {'name': 'Paciente do Facebook', 'phone': '', 'email': ''}
                        
                        for field in field_data:
                            if 'name' in field['name']: lead_info['name'] = field['values'][0]
                            if 'phone' in field['name']: lead_info['phone'] = field['values'][0]
                            if 'email' in field['name']: lead_info['email'] = field['values'][0]
                        
                        exists = Lead.query.filter_by(
                            clinic_id=clinic.id, 
                            name=lead_info['name']
                        ).first()
                        
                        if not exists:
                            new_lead = Lead(
                                clinic_id=clinic.id,
                                name=lead_info['name'],
                                phone=lead_info['phone'],
                                source=f"FB Ads: {ad.get('name')}",
                                status='new',
                                created_at=datetime.utcnow(),
                                notes="Importado automaticamente via Meta Ads"
                            )
                            db.session.add(new_lead)
                            new_leads_count += 1
                            
        except Exception as e:
            print(f"Erro ao importar leads: {e}")

        db.session.commit()

        return jsonify({
            'message': 'Sincronização Completa',
            'spend': spend,
            'clicks': clicks,
            'cpc': cpc,
            'leads_imported': new_leads_count
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f"Erro interno: {str(e)}"}), 500


# --- 3. NOVA FUNCIONALIDADE: INSTAGRAM & IA COPYWRITING ---

@marketing_bp.route('/marketing/instagram/media', methods=['GET'])
@jwt_required()
def get_instagram_media():
    """
    Busca os últimos posts do Instagram Business do cliente
    """
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        if not clinic.meta_access_token:
            return jsonify({'error': 'Instagram não conectado.'}), 400

        # 1. Achar o ID do Instagram vinculado à Página
        url_pages = "https://graph.facebook.com/v19.0/me/accounts"
        params_pages = {
            'access_token': clinic.meta_access_token,
            'fields': 'instagram_business_account{id},name,access_token'
        }
        resp_pages = requests.get(url_pages, params=params_pages)
        data_pages = resp_pages.json().get('data', [])

        ig_user_id = None
        
        for page in data_pages:
            if 'instagram_business_account' in page:
                ig_user_id = page['instagram_business_account']['id']
                break
        
        if not ig_user_id:
            return jsonify({'error': 'Nenhuma conta de Instagram Business encontrada vinculada à página.'}), 404

        # 2. Buscar mídias
        url_media = f"https://graph.facebook.com/v19.0/{ig_user_id}/media"
        params_media = {
            'access_token': clinic.meta_access_token,
            'fields': 'id,caption,media_type,media_url,thumbnail_url,permalink,timestamp',
            'limit': 12
        }
        resp_media = requests.get(url_media, params=params_media)
        media_items = resp_media.json().get('data', [])

        return jsonify(media_items), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@marketing_bp.route('/marketing/ai/generate', methods=['POST'])
@jwt_required()
def generate_copy_ai():
    """
    Simula uma IA de Copywriting para gerar legendas vendedoras
    """
    try:
        data = request.get_json()
        original_caption = data.get('caption', '')
        
        # Templates de Copywriting (Simulação de IA)
        prompts = [
            f"🚀 Transforme seu sorriso hoje! {original_caption}... Agende sua avaliação agora clicando no link da bio! 🦷✨",
            f"💡 Você sabia? {original_caption}. Cuide da sua saúde bucal com quem entende. Responda 'EU QUERO' para saber mais!",
            f"⚠️ Atenção: {original_caption}. Não deixe para depois o que pode custar seu dente amanhã. Vagas limitadas para essa semana!",
            f"✨ O sorriso dos seus sonhos está perto. {original_caption}. Tecnologia e conforto esperando por você aqui na clínica."
        ]
        
        ai_suggestion = random.choice(prompts)

        return jsonify({'suggestion': ai_suggestion}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- 4. REATIVAÇÃO (MANTIDO IGUAL) ---

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


# --- 5. ROTA DE CRESCIMENTO ---
@marketing_bp.route('/marketing/campaign/activate', methods=['POST'])
@jwt_required()
def activate_ads():
    return jsonify({'message': 'Use a conexão real com Meta Ads acima'}), 200