from flask import Blueprint, jsonify, request
from app.models import db, Lead, User, Patient, Appointment, MarketingCampaign, Clinic
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import requests
import os
import random

marketing_bp = Blueprint('marketing', __name__)

# --- 1. GESTÃO DE LEADS ---

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
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)
        data = request.get_json()
        
        short_lived_token = data.get('accessToken')
        if not short_lived_token:
            return jsonify({'error': 'Token não fornecido'}), 400

        # Troca por Long-Lived Token
        app_id = os.environ.get('META_APP_ID')
        app_secret = os.environ.get('META_APP_SECRET')
        long_lived_token = short_lived_token

        if app_id and app_secret:
            url = "https://graph.facebook.com/v19.0/oauth/access_token"
            params = {'grant_type': 'fb_exchange_token', 'client_id': app_id, 'client_secret': app_secret, 'fb_exchange_token': short_lived_token}
            resp = requests.get(url, params=params)
            if resp.status_code == 200:
                long_lived_token = resp.json().get('access_token')

        # Auto-Descoberta de Conta
        ad_account_id = data.get('adAccountId')
        if not ad_account_id:
            try:
                me_url = "https://graph.facebook.com/v19.0/me/adaccounts"
                me_params = {'access_token': long_lived_token, 'fields': 'account_id,name'}
                me_resp = requests.get(me_url, params=me_params)
                if me_resp.status_code == 200:
                    accounts = me_resp.json().get('data', [])
                    if accounts: ad_account_id = accounts[0].get('account_id')
            except: pass

        clinic.meta_access_token = long_lived_token
        if ad_account_id:
            clinic.meta_ad_account_id = str(ad_account_id).replace('act_', '')
        
        db.session.commit()
        return jsonify({'message': 'Conectado!', 'ad_account_id': ad_account_id}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@marketing_bp.route('/marketing/meta/sync', methods=['POST'])
@jwt_required()
def sync_meta_real():
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        if not clinic.meta_access_token or not clinic.meta_ad_account_id:
            return jsonify({'error': 'Conta não conectada.'}), 400

        ad_account_id = clinic.meta_ad_account_id.replace('act_', '')
        
        # 1. Busca Estatísticas (Ads)
        url_stats = f"https://graph.facebook.com/v19.0/act_{ad_account_id}/insights"
        params_stats = {'access_token': clinic.meta_access_token, 'date_preset': 'maximum', 'fields': 'spend,clicks,cpc'}
        
        response = requests.get(url_stats, params=params_stats)
        
        # SE DER ERRO NO FACEBOOK, NÃO ZERAMOS OS DADOS LOCAIS!
        if response.status_code != 200:
            return jsonify({'error': 'Erro ao conectar no Facebook Ads', 'details': response.json()}), response.status_code

        data = response.json().get('data', [])
        
        if data:
            stats = data[0]
            spend = float(stats.get('spend', 0.0))
            clicks = int(stats.get('clicks', 0))
            cpc = float(stats.get('cpc', 0.0))
            
            clinic.current_ad_balance = spend
            db.session.commit()
            
            return jsonify({'message': 'Sync OK', 'spend': spend, 'clicks': clicks, 'cpc': cpc}), 200
        
        return jsonify({'message': 'Sync OK (Sem dados)', 'spend': 0.0, 'clicks': 0, 'cpc': 0.0}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- 3. MÍDIAS SOCIAIS (INSTAGRAM & FACEBOOK) & IA ---

@marketing_bp.route('/marketing/instagram/media', methods=['GET'])
@jwt_required()
def get_instagram_media():
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        if not clinic.meta_access_token:
            return jsonify({'error': 'Conta não conectada.'}), 400

        # Busca Página -> Instagram Vinculado
        url_pages = "https://graph.facebook.com/v19.0/me/accounts"
        params = {'access_token': clinic.meta_access_token, 'fields': 'instagram_business_account{id}'}
        resp = requests.get(url_pages, params=params)
        data = resp.json().get('data', [])

        ig_id = None
        for page in data:
            if 'instagram_business_account' in page:
                ig_id = page['instagram_business_account']['id']
                break
        
        if not ig_id:
            return jsonify({'error': 'Nenhum Instagram Business vinculado à Página do Facebook.'}), 404

        url_media = f"https://graph.facebook.com/v19.0/{ig_id}/media"
        params_media = {'access_token': clinic.meta_access_token, 'fields': 'id,caption,media_type,media_url,thumbnail_url,permalink,timestamp', 'limit': 15}
        resp_media = requests.get(url_media, params_media)
        
        return jsonify(resp_media.json().get('data', [])), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@marketing_bp.route('/marketing/facebook/media', methods=['GET'])
@jwt_required()
def get_facebook_media():
    """
    NOVA ROTA: Busca posts da Página do Facebook
    """
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        if not clinic.meta_access_token:
            return jsonify({'error': 'Conta não conectada.'}), 400

        # Busca a primeira página administrada pelo usuário
        url_pages = "https://graph.facebook.com/v19.0/me/accounts"
        params = {'access_token': clinic.meta_access_token, 'fields': 'id,name'}
        resp = requests.get(url_pages, params=params)
        data = resp.json().get('data', [])

        if not data:
            return jsonify({'error': 'Nenhuma página do Facebook encontrada.'}), 404
            
        page_id = data[0]['id'] # Pega a primeira página

        # Busca posts da página (feed)
        url_posts = f"https://graph.facebook.com/v19.0/{page_id}/posts"
        params_posts = {
            'access_token': clinic.meta_access_token,
            'fields': 'id,message,full_picture,created_time,permalink_url',
            'limit': 15
        }
        resp_posts = requests.get(url_posts, params=params_posts)
        
        # Formata para ficar igual ao objeto do Instagram no front
        fb_data = resp_posts.json().get('data', [])
        formatted_data = []
        for post in fb_data:
            if 'full_picture' in post: # Só traz posts que tem imagem
                formatted_data.append({
                    'id': post['id'],
                    'media_url': post['full_picture'],
                    'thumbnail_url': post['full_picture'],
                    'caption': post.get('message', ''),
                    'media_type': 'IMAGE',
                    'permalink': post.get('permalink_url', '')
                })

        return jsonify(formatted_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@marketing_bp.route('/marketing/ai/generate', methods=['POST'])
@jwt_required()
def generate_copy_ai():
    try:
        data = request.get_json()
        caption = data.get('caption', '')
        
        prompts = [
            f"🚀 Transforme seu sorriso! {caption}... Agende sua avaliação no link da bio! 🦷✨",
            f"💡 Curiosidade: {caption}. Cuide da saúde bucal. Responda 'EU QUERO'!",
            f"✨ O sorriso dos sonhos: {caption}. Tecnologia e conforto aqui na clínica."
        ]
        return jsonify({'suggestion': random.choice(prompts)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- 4. EXTRAS ---
@marketing_bp.route('/marketing/campaign/recall', methods=['GET'])
@jwt_required()
def get_recall(): return jsonify([]), 200 

@marketing_bp.route('/marketing/campaign/activate', methods=['POST'])
@jwt_required()
def activate(): return jsonify({'msg': 'ok'}), 200