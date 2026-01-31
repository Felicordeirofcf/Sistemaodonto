from flask import Blueprint, jsonify, request
from app.models import db, Lead, User, Patient, Appointment, MarketingCampaign, Clinic
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import requests
import os
import random

marketing_bp = Blueprint('marketing', __name__)

GRAPH_VERSION = "v19.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"


def graph_get(path: str, access_token: str, params: dict | None = None, timeout=30):
    """Helper centralizado para chamadas no Graph API com tratamento de erro decente."""
    params = params or {}
    params["access_token"] = access_token
    url = f"{GRAPH_BASE}/{path.lstrip('/')}"
    resp = requests.get(url, params=params, timeout=timeout)

    try:
        data = resp.json()
    except Exception:
        return resp.status_code, {"error": {"message": resp.text}}

    # Erros do Graph API costumam vir em {"error": {...}}
    if resp.status_code >= 400 or (isinstance(data, dict) and data.get("error")):
        return resp.status_code, data

    return resp.status_code, data


def get_user_pages(user_token: str):
    """Lista páginas que o usuário gerencia. Retorna lista de dicts com id/name/access_token."""
    status, data = graph_get(
        "/me/accounts",
        user_token,
        params={"fields": "id,name,access_token"},
    )
    if status != 200:
        return [], data
    return data.get("data", []), None


def get_ig_business_id_from_page(page_id: str, page_token: str):
    """Busca instagram_business_account a partir de uma Page."""
    status, data = graph_get(
        f"/{page_id}",
        page_token,
        params={"fields": "instagram_business_account"},
    )
    if status != 200:
        return None, data
    ig = data.get("instagram_business_account")
    return (ig.get("id") if ig else None), None


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
        new_lead = Lead(
            clinic_id=user.clinic_id,
            name=data.get('name'),
            phone=data.get('phone'),
            source=data.get('source', 'Manual'),
            status='new'
        )
        db.session.add(new_lead)
        db.session.commit()
        return jsonify(new_lead.to_dict()), 201
    except Exception:
        db.session.rollback()
        return jsonify({'error': 'Erro ao criar lead'}), 500


@marketing_bp.route('/marketing/leads/<int:id>/move', methods=['PUT'])
@jwt_required()
def move_lead(id):
    user = User.query.get(get_jwt_identity())
    data = request.get_json()
    lead = Lead.query.filter_by(id=id, clinic_id=user.clinic_id).first()
    if not lead:
        return jsonify({'error': 'Lead não encontrado'}), 404
    lead.status = data.get('status')
    db.session.commit()
    return jsonify({'message': 'Ok'}), 200


# --- 2. CONEXÃO META ADS ---

@marketing_bp.route('/marketing/meta/connect', methods=['POST'])
@jwt_required()
def connect_meta_real():
    """
    Recebe token curto do front (login Meta) e troca por long-lived (quando possível).
    Salva em clinic.meta_access_token.
    """
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)
        data = request.get_json() or {}

        short_lived_token = data.get('accessToken')
        if not short_lived_token:
            return jsonify({'error': 'Token não fornecido'}), 400

        print(f"Token Recebido: {short_lived_token[:10]}...")

        app_id = os.environ.get('META_APP_ID')
        app_secret = os.environ.get('META_APP_SECRET')
        long_lived_token = short_lived_token

        # Tenta trocar por long-lived
        if app_id and app_secret:
            url = f"{GRAPH_BASE}/oauth/access_token"
            params = {
                'grant_type': 'fb_exchange_token',
                'client_id': app_id,
                'client_secret': app_secret,
                'fb_exchange_token': short_lived_token
            }
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                long_lived_token = resp.json().get('access_token') or short_lived_token

        clinic.meta_access_token = long_lived_token
        clinic.last_sync_at = datetime.utcnow()

        # IMPORTANTE: não selecione página aqui automaticamente no escuro.
        # O fluxo correto é: front chama /marketing/meta/pages e depois /select-page
        db.session.commit()
        return jsonify({'message': 'Conectado!'}), 200

    except Exception as e:
        print(f"Erro Connect: {e}")
        return jsonify({'error': str(e)}), 500


@marketing_bp.route('/marketing/meta/sync', methods=['POST'])
@jwt_required()
def sync_meta_real():
    """
    Mantive seu retorno fake, mas agora também informa se existe page selecionada.
    """
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        if not clinic.meta_access_token:
            return jsonify({'error': 'Desconectado'}), 401

        return jsonify({
            'message': 'Sync OK',
            'spend': clinic.current_ad_balance or 0.0,
            'clicks': 0,
            'cpc': 0.0,
            'page_selected': bool(getattr(clinic, "meta_page_id", None))
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@marketing_bp.route('/marketing/meta/disconnect', methods=['POST'])
@jwt_required()
def disconnect_meta():
    user = User.query.get(get_jwt_identity())
    clinic = Clinic.query.get(user.clinic_id)

    clinic.meta_access_token = None

    # limpa também seleção de página (se existir no modelo)
    if hasattr(clinic, "meta_page_id"):
        clinic.meta_page_id = None
    if hasattr(clinic, "meta_page_name"):
        clinic.meta_page_name = None
    if hasattr(clinic, "meta_page_access_token"):
        clinic.meta_page_access_token = None

    db.session.commit()
    return jsonify({'message': 'Desconectado'}), 200


# --- 2.1 NOVOS ENDPOINTS: LISTAR PÁGINAS E SELECIONAR PÁGINA ---

@marketing_bp.route('/marketing/meta/pages', methods=['GET'])
@jwt_required()
def meta_pages():
    """
    Retorna lista de páginas do usuário via /me/accounts.
    Front-end deve chamar isso depois do connect.
    """
    user = User.query.get(get_jwt_identity())
    clinic = Clinic.query.get(user.clinic_id)

    if not clinic.meta_access_token:
        return jsonify({'ok': False, 'error': 'Desconectado'}), 401

    pages, err = get_user_pages(clinic.meta_access_token)
    if err:
        # err pode conter detalhes do Graph
        return jsonify({'ok': False, 'error': 'Erro ao listar páginas', 'details': err}), 400

    # Retorne sem page_token (por segurança). O token da Page a gente salva no banco no select-page.
    sanitized = [{'id': p.get('id'), 'name': p.get('name')} for p in pages]
    return jsonify({'ok': True, 'pages': sanitized}), 200


@marketing_bp.route('/marketing/meta/select-page', methods=['POST'])
@jwt_required()
def meta_select_page():
    """
    Recebe page_id do front e salva no banco, junto com page_access_token obtido via /me/accounts.
    """
    user = User.query.get(get_jwt_identity())
    clinic = Clinic.query.get(user.clinic_id)

    if not clinic.meta_access_token:
        return jsonify({'ok': False, 'error': 'Desconectado'}), 401

    payload = request.get_json() or {}
    page_id = payload.get("page_id")
    if not page_id:
        return jsonify({'ok': False, 'error': 'page_id obrigatório'}), 400

    pages, err = get_user_pages(clinic.meta_access_token)
    if err:
        return jsonify({'ok': False, 'error': 'Erro ao listar páginas', 'details': err}), 400

    selected = next((p for p in pages if str(p.get("id")) == str(page_id)), None)
    if not selected:
        return jsonify({'ok': False, 'error': 'Página não encontrada para este usuário'}), 404

    # Salva no banco (você vai criar esses campos no model Clinic)
    clinic.meta_page_id = selected.get("id")
    clinic.meta_page_name = selected.get("name")
    clinic.meta_page_access_token = selected.get("access_token")

    db.session.commit()
    return jsonify({'ok': True, 'message': 'Página selecionada com sucesso'}), 200


# --- 3. MÍDIAS (CORRIGIDO) ---

@marketing_bp.route('/marketing/facebook/media', methods=['GET'])
@jwt_required()
def get_facebook_media():
    """
    Agora usa UMA página selecionada. Se não tiver, devolve 409 (estado inválido).
    """
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        if not clinic.meta_access_token:
            return jsonify({'error': 'Desconectado'}), 401

        page_id = getattr(clinic, "meta_page_id", None)
        page_token = getattr(clinic, "meta_page_access_token", None)

        if not page_id or not page_token:
            return jsonify({
                'error': 'Nenhuma página selecionada. Vá em Meta > Selecionar Página.'
            }), 409

        print(f"--- BUSCANDO POSTS FACEBOOK (PAGE) --- {getattr(clinic, 'meta_page_name', '')} ({page_id})")

        status, data = graph_get(
            f"/{page_id}/posts",
            page_token,
            params={'fields': 'id,message,full_picture,created_time,permalink_url', 'limit': 15}
        )

        if status != 200:
            return jsonify({'error': 'Erro ao buscar posts', 'details': data}), 400

        fb_posts = data.get('data', [])
        all_posts = []

        for post in fb_posts:
            if post.get('full_picture'):
                all_posts.append({
                    'id': post.get('id'),
                    'media_url': post.get('full_picture'),
                    'thumbnail_url': post.get('full_picture'),
                    'caption': post.get('message', '') or '',
                    'media_type': 'IMAGE',
                    'permalink': post.get('permalink_url', '') or ''
                })

        return jsonify(all_posts), 200

    except Exception as e:
        print(f"ERRO CRÍTICO FACEBOOK: {str(e)}")
        return jsonify({'error': str(e)}), 500


@marketing_bp.route('/marketing/instagram/media', methods=['GET'])
@jwt_required()
def get_instagram_media():
    """
    Agora usa UMA página selecionada e o token da página.
    Também corrige o bug do requests.get sem params=.
    """
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        if not clinic.meta_access_token:
            return jsonify({'error': 'Desconectado'}), 401

        page_id = getattr(clinic, "meta_page_id", None)
        page_token = getattr(clinic, "meta_page_access_token", None)

        if not page_id or not page_token:
            return jsonify({
                'error': 'Nenhuma página selecionada. Vá em Meta > Selecionar Página.'
            }), 409

        print(f"--- BUSCANDO INSTAGRAM (VIA PAGE) --- {getattr(clinic, 'meta_page_name', '')} ({page_id})")

        ig_id, err = get_ig_business_id_from_page(page_id, page_token)
        if err:
            return jsonify({'error': 'Erro ao buscar instagram_business_account', 'details': err}), 400

        if not ig_id:
            return jsonify({
                'error': 'Essa Página não tem Instagram Business vinculado. Verifique se o IG é Business/Creator e está conectado à Página.'
            }), 409

        status, data = graph_get(
            f"/{ig_id}/media",
            page_token,
            params={'fields': 'id,caption,media_type,media_url,thumbnail_url,permalink,timestamp', 'limit': 15}
        )

        if status != 200:
            return jsonify({'error': 'Erro ao buscar mídia do Instagram', 'details': data}), 400

        return jsonify(data.get('data', [])), 200

    except Exception as e:
        print(f"ERRO CRÍTICO INSTAGRAM: {str(e)}")
        return jsonify({'error': str(e)}), 500


# --- AI (MANTIDO) ---
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
