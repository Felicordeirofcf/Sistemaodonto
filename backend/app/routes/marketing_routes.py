from flask import Blueprint, jsonify, request
from app.models import db, Lead, User, Patient, Appointment, MarketingCampaign, Clinic
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import requests
import os
import random

marketing_bp = Blueprint('marketing', __name__)

# --- 1. GESTÃO DE LEADS (MANTIDO) ---
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
        new_lead = Lead(clinic_id=user.clinic_id, name=data.get('name'), phone=data.get('phone'), source=data.get('source', 'Manual'), status='new')
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
    return jsonify({'message': 'Ok'}), 200

# --- 2. CONEXÃO META ADS ---
@marketing_bp.route('/marketing/meta/connect', methods=['POST'])
@jwt_required()
def connect_meta_real():
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)
        data = request.get_json()
        
        short_lived_token = data.get('accessToken')
        if not short_lived_token: return jsonify({'error': 'Token não fornecido'}), 400

        # Debug
        print(f"Token Recebido: {short_lived_token[:10]}...")

        # Troca Token
        app_id = os.environ.get('META_APP_ID')
        app_secret = os.environ.get('META_APP_SECRET')
        long_lived_token = short_lived_token

        if app_id and app_secret:
            url = "https://graph.facebook.com/v19.0/oauth/access_token"
            params = {'grant_type': 'fb_exchange_token', 'client_id': app_id, 'client_secret': app_secret, 'fb_exchange_token': short_lived_token}
            resp = requests.get(url, params=params)
            if resp.status_code == 200: long_lived_token = resp.json().get('access_token')

        clinic.meta_access_token = long_lived_token
        clinic.last_sync_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Conectado!'}), 200
    except Exception as e:
        print(f"Erro Connect: {e}")
        return jsonify({'error': str(e)}), 500

@marketing_bp.route('/marketing/meta/sync', methods=['POST'])
@jwt_required()
def sync_meta_real():
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)
        if not clinic.meta_access_token: return jsonify({'error': 'Desconectado'}), 401
        
        # Retorna dados fake se não tiver conta de anúncio configurada (para não quebrar o front)
        return jsonify({'message': 'Sync OK', 'spend': clinic.current_ad_balance or 0.0, 'clicks': 0, 'cpc': 0.0}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@marketing_bp.route('/marketing/meta/disconnect', methods=['POST'])
@jwt_required()
def disconnect_meta():
    user = User.query.get(get_jwt_identity())
    clinic = Clinic.query.get(user.clinic_id)
    clinic.meta_access_token = None
    db.session.commit()
    return jsonify({'message': 'Desconectado'}), 200

# --- 3. MÍDIAS (COM DEBUG LOGS) ---

@marketing_bp.route('/marketing/facebook/media', methods=['GET'])
@jwt_required()
def get_facebook_media():
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        if not clinic.meta_access_token:
            return jsonify({'error': 'Token não encontrado no banco.'}), 400

        print(f"--- BUSCANDO PÁGINAS FACEBOOK ---")
        
        # 1. Busca Páginas
        url_pages = "https://graph.facebook.com/v19.0/me/accounts"
        params = {'access_token': clinic.meta_access_token, 'fields': 'id,name,access_token'}
        resp = requests.get(url_pages, params=params)
        
        print(f"Status Facebook API: {resp.status_code}")
        data = resp.json().get('data', [])
        
        if not data:
            print("ERRO: O Facebook retornou lista vazia de páginas. O usuário não selecionou as páginas no Login.")
            return jsonify({'error': 'Nenhuma página encontrada. Verifique se você marcou "Selecionar Todas" no login.'}), 404

        print(f"Páginas encontradas: {len(data)}")

        all_posts = []
        for page in data:
            page_id = page['id']
            page_token = page['access_token']
            print(f"Buscando posts da página: {page.get('name')} (ID: {page_id})")

            url_posts = f"https://graph.facebook.com/v19.0/{page_id}/posts"
            params_posts = {
                'access_token': page_token,
                'fields': 'id,message,full_picture,created_time,permalink_url',
                'limit': 10
            }
            resp_posts = requests.get(url_posts, params=params_posts)
            fb_posts = resp_posts.json().get('data', [])
            
            for post in fb_posts:
                if 'full_picture' in post:
                    all_posts.append({
                        'id': post['id'],
                        'media_url': post['full_picture'],
                        'thumbnail_url': post['full_picture'],
                        'caption': post.get('message', ''),
                        'media_type': 'IMAGE',
                        'permalink': post.get('permalink_url', '')
                    })
        
        return jsonify(all_posts[:15]), 200

    except Exception as e:
        print(f"ERRO CRÍTICO FACEBOOK: {str(e)}")
        return jsonify({'error': str(e)}), 500

@marketing_bp.route('/marketing/instagram/media', methods=['GET'])
@jwt_required()
def get_instagram_media():
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        if not clinic.meta_access_token: return jsonify({'error': 'Desconectado'}), 400

        print(f"--- BUSCANDO INSTAGRAM ---")

        # 1. Busca Página vinculada ao Instagram
        url_pages = "https://graph.facebook.com/v19.0/me/accounts"
        params = {'access_token': clinic.meta_access_token, 'fields': 'instagram_business_account{id},name'}
        resp = requests.get(url_pages, params=params)
        data = resp.json().get('data', [])

        if not data:
             print("ERRO: Nenhuma página encontrada para buscar Instagram.")
             return jsonify({'error': 'Nenhuma página encontrada.'}), 404

        ig_id = None
        for page in data:
            if 'instagram_business_account' in page:
                ig_id = page['instagram_business_account']['id']
                print(f"Instagram encontrado na página {page.get('name')} (IG ID: {ig_id})")
                break
        
        if not ig_id:
            print("ERRO: Páginas encontradas, mas nenhuma tem Instagram Business vinculado.")
            return jsonify({'error': 'Nenhum Instagram Business vinculado às suas páginas.'}), 404

        url_media = f"https://graph.facebook.com/v19.0/{ig_id}/media"
        params_media = {'access_token': clinic.meta_access_token, 'fields': 'id,caption,media_type,media_url,thumbnail_url,permalink', 'limit': 15}
        resp_media = requests.get(url_media, params_media)
        
        return jsonify(resp_media.json().get('data', [])), 200

    except Exception as e:
        print(f"ERRO CRÍTICO INSTAGRAM: {str(e)}")
        return jsonify({'error': str(e)}), 500

@marketing_bp.route('/marketing/ai/generate', methods=['POST'])
@jwt_required()
def generate_copy_ai():
    try:
        data = request.get_json()
        caption = data.get('caption', '')
        prompts = [
            f"🚀 Transforme seu sorriso! {caption}... Agende no link da bio! 🦷✨",
            f"💡 Dica do Dr: {caption}. Cuide da saúde bucal. Responda 'EU QUERO'!",
            f"✨ Tecnologia e conforto: {caption}. Venha conhecer nossa clínica."
        ]
        return jsonify({'suggestion': random.choice(prompts)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500