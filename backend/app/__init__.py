from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import logging

# Configuração de Log para aparecer no painel do Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')

    # --- CONFIGURAÇÃO DO BANCO DE DADOS ---
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///odonto_saas.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secreta')

    # Configuração de Timeout para conexões
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # --- BLOCO DE CORREÇÃO AUTOMÁTICA (PARA RENDER FREE) ---
    with app.app_context():
        from sqlalchemy import text
        try:
            logger.info("🔍 Verificando integridade das tabelas...")
            # Tenta adicionar a coluna is_active na tabela users caso ela não exista
            db.session.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;'))
            # Tenta adicionar a coluna is_active na tabela clinics caso ela não exista (visto no seu models)
            db.session.execute(text('ALTER TABLE clinics ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;'))
            db.session.commit()
            logger.info("✅ Colunas de segurança (is_active) verificadas/criadas.")
        except Exception as e:
            db.session.rollback()
            logger.warning(f"⚠️ Nota sobre sincronização: {e}")
    # -------------------------------------------------------

    from .models import Clinic, User, Patient, InventoryItem, Lead, Appointment, Transaction, Procedure, MarketingCampaign

    # --- REGISTRO DE BLUEPRINTS ---
    from .routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from .routes.patient_routes import patient_bp
    app.register_blueprint(patient_bp, url_prefix='/api')
    
    from .routes.stock_routes import stock_bp
    app.register_blueprint(stock_bp, url_prefix='/api')

    from .routes.dashboard_routes import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/api')

    from .routes.atende_chat_routes import atende_chat_bp
    app.register_blueprint(atende_chat_bp, url_prefix='/api')

    from .routes.marketing_routes import marketing_bp
    app.register_blueprint(marketing_bp, url_prefix='/api')

    from .routes.agenda_routes import agenda_bp
    app.register_blueprint(agenda_bp, url_prefix='/api')

    from .routes.financial_routes import financial_bp
    app.register_blueprint(financial_bp, url_prefix='/api')

    from .routes.team_routes import team_bp
    app.register_blueprint(team_bp, url_prefix='/api') 

    from .routes.procedure_routes import procedure_bp
    app.register_blueprint(procedure_bp, url_prefix='/api')

    # --- ROTAS DE UTILIDADE ---

    @app.route('/api/force_reset_db')
    def force_reset():
        """Apaga e recria com logs para debug"""
        confirm = request.args.get('confirm')
        if confirm != 'true':
            return "Erro: Adicione ?confirm=true", 403
        
        try:
            logger.info("Iniciando Reset Total do Banco...")
            db.session.remove()
            db.drop_all()
            db.create_all()
            logger.info("✅ Banco resetado com sucesso!")
            return "✅ BANCO RESETADO COM SUCESSO! Prossiga para /api/seed_db_web", 200
        except Exception as e:
            logger.error(f"❌ Erro Crítico no Reset: {str(e)}")
            return f"Erro no servidor: {str(e)}", 500

    @app.route('/api/seed_db_web')
    def seed_db_web():
        """Popula o banco via URL"""
        from werkzeug.security import generate_password_hash
        from datetime import datetime, timedelta
        try:
            logger.info("Iniciando Seed de Dados...")
            db.create_all()

            if not Clinic.query.filter_by(name="OdontoSys Intelligence Demo").first():
                demo_clinic = Clinic(
                    name="OdontoSys Intelligence Demo",
                    plan_type="gold",
                    max_dentists=10,
                    is_active=True
                )
                db.session.add(demo_clinic)
                db.session.flush()

                admin = User(
                    name="Dr. Ricardo (Admin)",
                    email="admin@odonto.com",
                    password_hash=generate_password_hash("admin123"),
                    role='admin',
                    is_active=True,
                    clinic_id=demo_clinic.id
                )
                db.session.add(admin)

                eight_months_ago = datetime.utcnow() - timedelta(days=240)
                p1 = Patient(
                    name="Carlos Eduardo", 
                    phone="11999999999", 
                    last_visit=eight_months_ago, 
                    clinic_id=demo_clinic.id
                )
                db.session.add(p1)
                
                db.session.commit()
                logger.info("✅ Seed Finalizado!")
                return "✅ BANCO POPULADO! Use admin@odonto.com / admin123", 200
            
            return "ℹ️ O banco já possui dados.", 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erro no Seed: {str(e)}")
            return f"Erro no seed: {str(e)}", 500

    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api') or request.path.startswith('/auth'):
            return jsonify({'error': 'Rota não encontrada'}), 404
        return app.send_static_file('index.html')

    return app
