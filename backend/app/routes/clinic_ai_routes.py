from flask import Blueprint, jsonify, request
from app.models import db, User, Clinic, ClinicAISettings
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from datetime import datetime

clinic_bp = Blueprint('clinic', __name__)

# -----------------------------
# Helpers IA Settings
# -----------------------------

def _default_ai_settings_payload():
    # Um prompt “profissional” base, neutro para SaaS (cada clínica pode customizar)
    system_prompt = (
        "Você é uma recepcionista virtual de uma clínica odontológica. "
        "Seu objetivo é atender com educação, clareza e empatia, em português do Brasil. "
        "Você deve: (1) entender a intenção do paciente, (2) coletar dados essenciais, "
        "(3) explicar procedimentos de forma simples, (4) agendar/remarcar/cancelar quando solicitado, "
        "(5) confirmar antes de salvar, (6) verificar conflitos de horário e oferecer alternativas. "
        "Se faltar alguma informação para concluir, faça perguntas objetivas. "
        "Não invente valores, não faça diagnóstico, e não prometa resultados clínicos. "
        "Quando houver dúvida, peça para um atendente humano continuar."
    )

    procedures_json = {
        "procedures": [
            {
                "name": "Aplicação de resina",
                "description": (
                    "A aplicação de resina é indicada para restaurar dentes com cárie, trincas pequenas "
                    "ou ajustes estéticos. O dentista avalia o dente, remove a parte comprometida (se houver), "
                    "aplica a resina e faz o acabamento."
                ),
                "duration_min": 40,
                "questions": [
                    "É em qual dente/região (frente, trás, superior, inferior)?",
                    "Você sente dor ou sensibilidade nesse dente?"
                ],
                "notes": "Não informar preços. Orientar avaliação prévia se necessário."
            },
            {
                "name": "Botox",
                "description": (
                    "O botox pode ser utilizado para fins estéticos e também em casos específicos, "
                    "como bruxismo ou sorriso gengival, conforme avaliação profissional. "
                    "A aplicação é rápida, e o resultado costuma aparecer gradualmente."
                ),
                "duration_min": 30,
                "questions": [
                    "Você busca botox estético ou por indicação (ex: bruxismo)?",
                    "É a primeira vez que você faz aplicação?"
                ],
                "notes": "Evitar prometer resultados; recomendar avaliação."
            },
            {
                "name": "Limpeza de dente",
                "description": (
                    "A limpeza (profilaxia) remove placa e tártaro, ajudando na prevenção de gengivite "
                    "e outras alterações. Geralmente é rápida e pode incluir polimento."
                ),
                "duration_min": 30,
                "questions": [
                    "Há quanto tempo você fez a última limpeza?",
                    "Você sente sangramento na gengiva ao escovar?"
                ],
                "notes": "Se houver dor intensa/sangramento forte, orientar avaliação."
            },
            {
                "name": "Clareamento",
                "description": (
                    "O clareamento pode ser feito em consultório e/ou com moldeiras em casa, "
                    "dependendo da indicação. Antes é importante avaliar sensibilidade, "
                    "restaurações e saúde gengival."
                ),
                "duration_min": 45,
                "questions": [
                    "Você já fez clareamento antes?",
                    "Tem sensibilidade nos dentes?"
                ],
                "notes": "Não prometer tom final; depende de avaliação."
            }
        ]
    }

    business_rules_json = {
        "default_duration_min": 30,
        "confirm_before_booking": True,
        "business_hours": {
            "mon_fri": {"start": "08:00", "end": "18:00"},
            "sat": {"start": "08:00", "end": "12:00"},
            "sun": None
        },
        "conflict_policy": "offer_alternatives",  # ou "ask_human"
        "timezone": "America/Sao_Paulo"
    }

    return system_prompt, procedures_json, business_rules_json


def _get_current_clinic():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user or not user.clinic:
        return None
    return user.clinic


def _ai_settings_to_dict(s: ClinicAISettings):
    return {
        "enabled": bool(s.enabled),
        "timezone": s.timezone,
        "system_prompt": s.system_prompt or "",
        "procedures_json": s.procedures_json or {},
        "business_rules_json": s.business_rules_json or {},
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


# -----------------------------
# Rotas existentes
# -----------------------------

@clinic_bp.route('/clinic/team-stats', methods=['GET'])
@jwt_required()
def get_team_stats():
    claims = get_jwt()
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    # Busca a clínica do usuário logado
    clinic = user.clinic

    # Lista todos os membros da equipe daquela clínica
    members = User.query.filter_by(clinic_id=clinic.id).all()

    # Conta apenas os que possuem cargo de dentista para o limite do plano
    dentist_count = User.query.filter_by(clinic_id=clinic.id, role='dentist').count()

    return jsonify({
        'plan_type': clinic.plan_type,
        'max_dentists': clinic.max_dentists,
        'current_count': dentist_count,
        'members': [{
            'id': m.id,
            'name': m.name,
            'email': m.email,
            'role': m.role
        } for m in members]
    }), 200


# -----------------------------
# ✅ NOVAS ROTAS: AI SETTINGS
# -----------------------------

@clinic_bp.route('/clinic/ai-settings', methods=['GET'])
@jwt_required()
def get_ai_settings():
    clinic = _get_current_clinic()
    if not clinic:
        return jsonify({"error": "clinic_not_found"}), 404

    settings = ClinicAISettings.query.filter_by(clinic_id=clinic.id).first()
    if not settings:
        system_prompt, procedures_json, business_rules_json = _default_ai_settings_payload()
        settings = ClinicAISettings(
            clinic_id=clinic.id,
            enabled=True,
            system_prompt=system_prompt,
            procedures_json=procedures_json,
            business_rules_json=business_rules_json,
            timezone=business_rules_json.get("timezone", "America/Sao_Paulo"),
        )
        db.session.add(settings)
        db.session.commit()

    return jsonify(_ai_settings_to_dict(settings)), 200


@clinic_bp.route('/clinic/ai-settings', methods=['PUT'])
@jwt_required()
def update_ai_settings():
    clinic = _get_current_clinic()
    if not clinic:
        return jsonify({"error": "clinic_not_found"}), 404

    settings = ClinicAISettings.query.filter_by(clinic_id=clinic.id).first()
    if not settings:
        # cria default e atualiza em seguida
        system_prompt, procedures_json, business_rules_json = _default_ai_settings_payload()
        settings = ClinicAISettings(
            clinic_id=clinic.id,
            enabled=True,
            system_prompt=system_prompt,
            procedures_json=procedures_json,
            business_rules_json=business_rules_json,
            timezone=business_rules_json.get("timezone", "America/Sao_Paulo"),
        )
        db.session.add(settings)
        db.session.flush()

    data = request.get_json(silent=True) or {}

    # Campos permitidos
    if "enabled" in data:
        settings.enabled = bool(data.get("enabled"))

    if "timezone" in data and isinstance(data.get("timezone"), str) and data["timezone"].strip():
        settings.timezone = data["timezone"].strip()

    if "system_prompt" in data and isinstance(data.get("system_prompt"), str):
        # não deixa vazio total (evita quebrar)
        sp = data["system_prompt"].strip()
        if len(sp) < 20:
            return jsonify({"error": "system_prompt_too_short"}), 400
        settings.system_prompt = sp

    if "procedures_json" in data and isinstance(data.get("procedures_json"), dict):
        # validação mínima: precisa ter procedures como lista
        pj = data["procedures_json"]
        if "procedures" in pj and isinstance(pj["procedures"], list):
            settings.procedures_json = pj
        else:
            return jsonify({"error": "invalid_procedures_json"}), 400

    if "business_rules_json" in data and isinstance(data.get("business_rules_json"), dict):
        settings.business_rules_json = data["business_rules_json"]

    db.session.commit()
    return jsonify(_ai_settings_to_dict(settings)), 200
