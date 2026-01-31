from flask import Blueprint, jsonify, request
from app.models import db, Lead, User, Patient, Appointment, MarketingCampaign, Clinic
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import requests
import os
import random
import traceback

marketing_bp = Blueprint('marketing', __name__)

GRAPH_VERSION = "v19.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"


# ---------------------------
# Helpers Meta Graph API
# ---------------------------

def graph_get(path: str, access_token: str, params: dict | None = None, timeout=30):
    """
    Helper centralizado para chamadas no Graph API:
    - Sempre retorna (status_code, json)
    - Se falhar parse JSON, devolve {"error": {"message": raw}}
    """
    params = params or {}
    params["access_token"] = access_token
    url = f"{GRAPH_BASE}/{path.lstrip('/')}"

    try:
        resp = requests.get(url, params=params, timeout=timeout)
    except Exception as e:
        return 599, {"error": {"message": f"Falha de rede ao chamar Graph API: {str(e)}"}}

    try:
        data = resp.json()
    except Exception:
        data = {"error": {"message": resp.text}}

    # Graph error normalmente vem como {"error": {...}}
    if resp.status_code >= 400 or (isinstance(data, dict) and data.get("error")):
        return resp.status_code, data

    return resp.status_code, data


def get_user_pages(user_token: str):
    """
    Lista páginas que o usuário gerencia.
    Retorna: (pages_list, err_payload)
    """
    status, data = graph_get(
        "/me/accounts",
        user_token,
        params={"fields": "id,name,access_token"},
    )
    if status != 200:
        return [], data
    return data.get("data", []), None


def get_ig_business_id_from_page(page_id: str, page_token: str):
    """
    Busca instagram_business_account a partir de uma Page.
    Retorna: (ig_id, err_payload)
    """
    status, data = graph_get(
        f"/{page_id}",
        page_token,
        params={"fields": "instagram_business_account"},
    )
    if status != 200:
        return None, data

    ig = data.get("instagram_business_account")
    return (ig.get("id") if ig else None), None


def safe_error(message: str, details=None, status_code=400):
    """
    Padrão de resposta de erro JSON (sempre válido).
    """
    payload = {"ok": False, "error": message}
    if details is not None:
        payload["details"] = details
    return jsonify(payload), status_code


# ---------------------------
# 1) Leads (mantido)
# ---------------------------

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
        data = request.get_json() or {}
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
    data = request.get_json() or {}
    lead = Lead.query.filter_by(id=id, clinic_id=user.clinic_id).first()
    if not lead:
        return jsonify({'error': 'Lead não encontrado'}), 404
    lead.status = data.get('status')
    db.session.commit()
    return jsonify({'message': 'Ok'}), 200


# ---------------------------
# 2) Meta Connect / Sync / Disconnect
# ---------------------------

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
            return safe_error("Token não fornecido", status_code=400)

        print(f"[META] Token Recebido (prefix): {short_lived_token[:10]}...")

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
            else:
                # Loga erro da troca (não quebra conexão, mas ajuda no debug)
                try:
                    print("[META] Falha ao trocar token:", resp.json())
                except Exception:
                    print("[META] Falha ao trocar token:", resp.text)

        clinic.meta_access_token = long_lived_token
        clinic.last_sync_at = datetime.utcnow()

        # Não define página automaticamente.
        # Fluxo correto: front chama /marketing/meta/pages e /marketing/meta/select-page.
        db.session.commit()
        return jsonify({'message': 'Conectado!'}), 200

    except Exception as e:
        print(f"[META] Erro Connect: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@marketing_bp.route('/marketing/meta/sync', methods=['POST'])
@jwt_required()
def sync_meta_real():
    """
    Mantido seu retorno fake, mas informa se existe page selecionada.
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
        print("[META] Erro Sync:", str(e))
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@marketing_bp.route('/marketing/meta/disconnect', methods=['POST'])
@jwt_required()
def disconnect_meta():
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        clinic.meta_access_token = None

        # limpa seleção de página (se existir)
        if hasattr(clinic, "meta_page_id"):
            clinic.meta_page_id = None
        if hasattr(clinic, "meta_page_name"):
            clinic.meta_page_name = None
        if hasattr(clinic, "meta_page_access_token"):
            clinic.meta_page_access_token = None

        db.session.commit()
        return jsonify({'message': 'Desconectado'}), 200

    except Exception as e:
        print("[META] Erro Disconnect:", str(e))
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# ---------------------------
# 2.1) Meta Pages / Select Page / Debug
# ---------------------------

@marketing_bp.route('/marketing/meta/pages', methods=['GET'])
@jwt_required()
def meta_pages():
    """
    Retorna lista de páginas do usuário via /me/accounts.
    """
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        if not clinic.meta_access_token:
            return safe_error("Desconectado", status_code=401)

        pages, err = get_user_pages(clinic.meta_access_token)

        # DEBUG NO SERVIDOR (pra você enxergar o code real)
        print("==== [META] /pages ====")
        print("clinic_id:", clinic.id)
        print("pages_count:", len(pages))
        if err:
            print("graph_error:", err)

        if err:
            # devolve 400 com details reais do Graph
            return safe_error("Erro ao listar páginas", details=err, status_code=400)

        sanitized = [{'id': p.get('id'), 'name': p.get('name')} for p in pages]
        return jsonify({'ok': True, 'pages': sanitized}), 200

    except Exception as e:
        print("[META] Erro /pages:", str(e))
        print(traceback.format_exc())
        return safe_error("Erro interno ao listar páginas", details=str(e), status_code=500)


@marketing_bp.route('/marketing/meta/select-page', methods=['POST'])
@jwt_required()
def meta_select_page():
    """
    Recebe page_id do front e salva no banco, junto com page_access_token obtido via /me/accounts.
    """
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        if not clinic.meta_access_token:
            return safe_error("Desconectado", status_code=401)

        payload = request.get_json() or {}
        page_id = payload.get("page_id")
        if not page_id:
            return safe_error("page_id obrigatório", status_code=400)

        pages, err = get_user_pages(clinic.meta_access_token)
        if err:
            return safe_error("Erro ao listar páginas", details=err, status_code=400)

        selected = next((p for p in pages if str(p.get("id")) == str(page_id)), None)
        if not selected:
            return safe_error("Página não encontrada para este usuário", status_code=404)

        # Salva no banco (precisa existir no model Clinic)
        clinic.meta_page_id = selected.get("id")
        clinic.meta_page_name = selected.get("name")
        clinic.meta_page_access_token = selected.get("access_token")
        db.session.commit()

        return jsonify({'ok': True, 'message': 'Página selecionada com sucesso'}), 200

    except Exception as e:
        print("[META] Erro select-page:", str(e))
        print(traceback.format_exc())
        return safe_error("Erro interno ao selecionar página", details=str(e), status_code=500)


@marketing_bp.route('/marketing/meta/debug', methods=['GET'])
@jwt_required()
def meta_debug():
    """
    Endpoint de debug para ver permissões e status do token.
    Use isso só pra diagnóstico.
    """
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        if not clinic.meta_access_token:
            return safe_error("Desconectado", status_code=401)

        # Permissões do usuário
        st_perm, perm = graph_get("/me/permissions", clinic.meta_access_token)

        # Dados básicos do usuário
        st_me, me = graph_get("/me", clinic.meta_access_token, params={"fields": "id,name"})

        return jsonify({
            "ok": True,
            "me_status": st_me,
            "me": me,
            "permissions_status": st_perm,
            "permissions": perm
        }), 200

    except Exception as e:
        print("[META] Erro meta_debug:", str(e))
        print(traceback.format_exc())
        return safe_error("Erro interno no debug Meta", details=str(e), status_code=500)


# ---------------------------
# 3) Mídias (Facebook / Instagram)
# ---------------------------

@marketing_bp.route('/marketing/facebook/media', methods=['GET'])
@jwt_required()
def get_facebook_media():
    """
    Usa UMA página selecionada. Se não tiver, devolve 409.
    """
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        if not clinic.meta_access_token:
            return jsonify({'error': 'Desconectado'}), 401

        page_id = getattr(clinic, "meta_page_id", None)
        page_token = getattr(clinic, "meta_page_access_token", None)

        if not page_id or not page_token:
            return jsonify({'error': 'Nenhuma página selecionada. Selecione uma Página do Facebook na aba Funil.'}), 409

        print(f"[META] Facebook posts: {getattr(clinic, 'meta_page_name', '')} ({page_id})")

        status, data = graph_get(
            f"/{page_id}/posts",
            page_token,
            params={'fields': 'id,message,full_picture,created_time,permalink_url', 'limit': 15}
        )

        if status != 200:
            return safe_error("Erro ao buscar posts do Facebook", details=data, status_code=400)

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
        print(f"[META] ERRO CRÍTICO FACEBOOK: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


@marketing_bp.route('/marketing/instagram/media', methods=['GET'])
@jwt_required()
def get_instagram_media():
    """
    Usa UMA página selecionada e o token da página.
    """
    try:
        user = User.query.get(get_jwt_identity())
        clinic = Clinic.query.get(user.clinic_id)

        if not clinic.meta_access_token:
            return jsonify({'error': 'Desconectado'}), 401

        page_id = getattr(clinic, "meta_page_id", None)
        page_token = getattr(clinic, "meta_page_access_token", None)

        if not page_id or not page_token:
            return jsonify({'error': 'Nenhuma página selecionada. Selecione uma Página do Facebook na aba Funil.'}), 409

        print(f"[META] Instagram via Page: {getattr(clinic, 'meta_page_name', '')} ({page_id})")

        ig_id, err = get_ig_business_id_from_page(page_id, page_token)
        if err:
            return safe_error("Erro ao buscar instagram_business_account", details=err, status_code=400)

        if not ig_id:
            return jsonify({
                'error': 'Essa Página não tem Instagram Business vinculado. O IG precisa ser Business/Creator e estar conectado à Página.'
            }), 409

        status, data = graph_get(
            f"/{ig_id}/media",
            page_token,
            params={'fields': 'id,caption,media_type,media_url,thumbnail_url,permalink,timestamp', 'limit': 15}
        )

        if status != 200:
            return safe_error("Erro ao buscar mídia do Instagram", details=data, status_code=400)

        return jsonify(data.get('data', [])), 200

    except Exception as e:
        print(f"[META] ERRO CRÍTICO INSTAGRAM: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500


# ---------------------------
# AI (mantido)
# ---------------------------

@marketing_bp.route('/marketing/ai/generate', methods=['POST'])
@jwt_required()
def generate_copy_ai():
    try:
        data = request.get_json() or {}
        caption = data.get('caption', '')
        prompts = [
            f"🚀 Transforme seu sorriso! {caption}... Agende no link da bio! 🦷✨",
            f"💡 Dica do Dr: {caption}. Cuide da saúde bucal. Responda 'EU QUERO'!",
            f"✨ Tecnologia e conforto: {caption}. Venha conhecer nossa clínica."
        ]
        return jsonify({'suggestion': random.choice(prompts)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
