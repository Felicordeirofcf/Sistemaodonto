from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import logging

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

    # 3. IMPORTAÇÃO DOS MODELS (DENTRO DA FUNÇÃO para evitar ciclo)
    # Nunca importe 'db' aqui, pois ele já foi criado lá em cima!
    from .models import (
        Clinic, User, Patient, InventoryItem, Appointment, Transaction,
        WhatsAppConnection, WhatsAppContact, MessageLog, ScheduledMessage
    )

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

    # ✅ WhatsApp (CORREÇÃO AQUI): Adicionando url_prefix para bater com o Frontend
    from .routes.marketing.whatsapp import bp as marketing_whatsapp_bp
    app.register_blueprint(marketing_whatsapp_bp, url_prefix="/api/marketing")

    # --- ROTAS DE SISTEMA (RESET E SEED) ---
    @app.route("/api/force_reset_db")
    def force_reset():
        confirm = request.args.get("confirm")
        if confirm != "true":
            return jsonify({"error": "Confirmação necessária (?confirm=true)"}), 403

        try:
            from sqlalchemy import text
            db.session.remove()
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
                    phone="11999999999",
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