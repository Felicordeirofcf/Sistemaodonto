from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import logging
from sqlalchemy import inspect

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. CRIAÇÃO DAS EXTENSÕES (O db nasce aqui!)
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__, static_folder="static", static_url_path="")

    # --- CONFIGURAÇÃO DO BANCO ---
    database_url = os.environ.get("DATABASE_URL")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///odonto_saas.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "super-secreta")

    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # --- CORS ---
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=False,
        allow_headers=["Content-Type", "Authorization", "X-Internal-Secret"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )

    # 2. INICIALIZAÇÃO DAS EXTENSÕES
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # 3. CONTEXTO DA APLICAÇÃO
    with app.app_context():
        # IMPORTAÇÃO DOS MODELS
        from .models import (
            Clinic, User, Patient, InventoryItem, Appointment, Transaction,
            WhatsAppConnection, WhatsAppContact, MessageLog, ScheduledMessage,
            AutomacaoRecall, CRMStage, CRMCard, CRMHistory,
            # ✅ NOVOS MODELS DE MARKETING
            Campaign, Lead, LeadEvent
        )

        # Cria as tabelas se não existirem (Segurança para SQLite/Dev)
        try:
            inspector = inspect(db.engine)
            if not inspector.has_table("users"):
                db.create_all()
                logger.info("✅ Banco de dados criado/atualizado com sucesso.")
        except Exception as e:
            logger.warning(f"⚠️ Aviso ao verificar banco: {e}")

    # --- REGISTRO DE BLUEPRINTS ---
    from .routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    from .routes.patient_routes import patient_bp
    app.register_blueprint(patient_bp, url_prefix="/api")

    from .routes.stock_routes import stock_bp
    app.register_blueprint(stock_bp, url_prefix="/api")

    from .routes.dashboard_routes import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix="/api")

    from .routes.atende_chat_routes import atende_chat_bp
    app.register_blueprint(atende_chat_bp, url_prefix="/api")

    from .routes.agenda_routes import agenda_bp
    app.register_blueprint(agenda_bp, url_prefix="/api")

    from .routes.financial_routes import financial_bp
    app.register_blueprint(financial_bp, url_prefix="/api")

    from .routes.team_routes import team_bp
    app.register_blueprint(team_bp, url_prefix="/api")

    # ✅ WhatsApp e Marketing (Core)
    from .routes.marketing.whatsapp import bp as marketing_whatsapp_bp
    app.register_blueprint(marketing_whatsapp_bp, url_prefix="/api/marketing")

    # ✅ Automações e Regras
    from .routes.marketing.automations import bp as automations_bp
    app.register_blueprint(automations_bp, url_prefix="/api/marketing")

    # ✅ Campanhas e Leads (Gestão + Links Públicos)
    from .routes.marketing.campaigns import bp as campaigns_bp
    # 1. Registra para API de gestão (ex: /api/marketing/campaigns)
    app.register_blueprint(campaigns_bp, url_prefix="/api/marketing")
    # 2. Registra na RAIZ para o link curto funcionar (ex: /c/xyz12)
    app.register_blueprint(campaigns_bp, name="campaigns_public", url_prefix="")

    # ✅ [NOVO] Webhook do WhatsApp (Adicione ISTO para o bot responder)
    from .routes.marketing.webhook import bp as webhook_bp
    app.register_blueprint(webhook_bp, url_prefix="/api/marketing")

    # --- ROTAS DE SISTEMA (RESET E SEED) ---
    @app.route("/api/force_reset_db")
    def force_reset():
        confirm = request.args.get("confirm")
        if confirm != "true":
            return jsonify({"error": "Confirmação necessária (?confirm=true)"}), 403

        try:
            from sqlalchemy import text
            db.session.remove()
            # Cuidado: Só funciona bem em Postgres
            db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
            db.session.commit()
            db.create_all()
            return jsonify({"message": "Banco resetado com sucesso! Agora rode o seed."}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    @app.route("/api/seed_db_web")
    def seed_db_web():
        from werkzeug.security import generate_password_hash
        from datetime import datetime, timedelta
        from .models import Clinic, User, Patient

        try:
            db.create_all()

            if not Clinic.query.filter_by(name="OdontoSys Intelligence Demo").first():
                demo_clinic = Clinic(
                    name="OdontoSys Intelligence Demo",
                    plan_type="gold",
                    max_dentists=10,
                    is_active=True,
                )
                db.session.add(demo_clinic)
                db.session.flush()

                admin = User(
                    name="Dr. Ricardo (Admin)",
                    email="admin@odonto.com",
                    password_hash=generate_password_hash("admin123"),
                    role="admin",
                    is_active=True,
                    clinic_id=demo_clinic.id,
                )
                db.session.add(admin)

                p1 = Patient(
                    name="Carlos Eduardo",
                    phone="5521999999999", 
                    last_visit=datetime.utcnow() - timedelta(days=240),
                    clinic_id=demo_clinic.id,
                )
                db.session.add(p1)

                db.session.commit()
                return jsonify({"message": "Seed finalizado", "user": "admin@odonto.com", "pass": "admin123"}), 200

            return jsonify({"message": "Dados já existentes"}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    # --- ROTA DE REPARO DE EMERGÊNCIA (Cria tabelas SQL na força bruta) ---
    @app.route("/api/fix_tables")
    def fix_tables():
        try:
            from sqlalchemy import text
            
            # 1. Cria tabela AutomacaoRecall
            sql_recall = text("""
                CREATE TABLE IF NOT EXISTS automacoes_recall (
                    id SERIAL PRIMARY KEY,
                    clinic_id INTEGER NOT NULL,
                    nome VARCHAR(100),
                    dias_ausente INTEGER,
                    horario_disparo VARCHAR(5),
                    mensagem_template TEXT,
                    ativo BOOLEAN DEFAULT TRUE
                );
            """)
            
            # 2. Cria tabela CRMStage
            sql_stage = text("""
                CREATE TABLE IF NOT EXISTS crm_stages (
                    id SERIAL PRIMARY KEY,
                    clinic_id INTEGER NOT NULL,
                    nome VARCHAR(50),
                    ordem INTEGER,
                    cor VARCHAR(7),
                    is_initial BOOLEAN DEFAULT FALSE,
                    is_success BOOLEAN DEFAULT FALSE
                );
            """)

            # 3. Cria tabela CRMCard
            sql_card = text("""
                CREATE TABLE IF NOT EXISTS crm_cards (
                    id SERIAL PRIMARY KEY,
                    clinic_id INTEGER NOT NULL,
                    paciente_id INTEGER,
                    stage_id INTEGER,
                    ultima_interacao TIMESTAMP WITHOUT TIME ZONE,
                    status VARCHAR(20) DEFAULT 'open'
                );
            """)

            # 4. Adiciona a coluna receive_marketing se ela não existir
            sql_coluna = text("""
                ALTER TABLE patients ADD COLUMN IF NOT EXISTS receive_marketing BOOLEAN DEFAULT TRUE;
            """)

            # 5. [NOVO] Tabelas de Marketing (Campanhas, Leads, Eventos)
            sql_marketing = text("""
                CREATE TABLE IF NOT EXISTS marketing_campaigns (
                    id SERIAL PRIMARY KEY, clinic_id INTEGER NOT NULL, name VARCHAR(100), slug VARCHAR(50), 
                    tracking_code VARCHAR(20), whatsapp_message_template TEXT, landing_page_data JSON, 
                    clicks_count INTEGER DEFAULT 0, leads_count INTEGER DEFAULT 0, active BOOLEAN DEFAULT TRUE, 
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS marketing_leads (
                    id SERIAL PRIMARY KEY, clinic_id INTEGER NOT NULL, campaign_id INTEGER, name VARCHAR(100), 
                    phone VARCHAR(30), status VARCHAR(20) DEFAULT 'novo', source VARCHAR(50), 
                    chatbot_state VARCHAR(50) DEFAULT 'START', chatbot_data JSON DEFAULT '{}', 
                    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(), updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS marketing_lead_events (
                    id SERIAL PRIMARY KEY, lead_id INTEGER, campaign_id INTEGER, event_type VARCHAR(50), 
                    metadata_json JSON, created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                );
            """)

            db.session.execute(sql_recall)
            db.session.execute(sql_stage)
            db.session.execute(sql_card)
            db.session.execute(sql_coluna)
            db.session.execute(sql_marketing) # Executa as novas
            db.session.commit()
            
            return jsonify({"message": "Tabelas recriadas via SQL com sucesso!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    # --- FRONTEND (SPA) ---
    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api") or request.path.startswith("/auth"):
            return jsonify({"error": "Rota não encontrada"}), 404
        return app.send_static_file("index.html")

    return app