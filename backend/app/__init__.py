from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import logging

# Configuração de Log para o Render
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

    # Engine Options para evitar conexões "zumbis" no Render Free
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Importação dos modelos para registro no SQLAlchemy
    from .models import Clinic, User, Patient, InventoryItem, Appointment, Transaction

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



    from .routes.agenda_routes import agenda_bp
    app.register_blueprint(agenda_bp, url_prefix='/api')

    from .routes.financial_routes import financial_bp
    app.register_blueprint(financial_bp, url_prefix='/api')

    from .routes.team_routes import team_bp
    app.register_blueprint(team_bp, url_prefix='/api') 



    # --- ROTAS DE MANUTENÇÃO (REVISADAS) ---

    @app.route('/api/force_reset_db')
    def force_reset():
        """Força a limpeza total do PostgreSQL via Cascade"""
        confirm = request.args.get('confirm')
        if confirm != 'true':
            return "Erro: Adicione ?confirm=true", 403
        
        try:
            from sqlalchemy import text
            logger.info("🔥 Iniciando destruição e recriação do Banco via CASCADE...")
            
            # Limpa sessões pendentes para não travar o banco
            db.session.remove()
            
            # Comando SQL bruto para limpar o Schema Public (Eficaz no Render)
            db.session.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
            db.session.commit()
            
            # Recria todas as tabelas com a estrutura do models.py atualizado
            db.create_all()
            
            logger.info("✅ Estrutura física do banco reconstruída com sucesso!")
            return "✅ BANCO RESETADO! Agora acesse /api/seed_db_web para criar o usuário.", 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Erro Crítico no Reset: {str(e)}")
            return f"Erro no servidor: {str(e)}", 500

    @app.route('/api/seed_db_web')
    def seed_db_web():
        """Popula os dados básicos de demonstração"""
        from werkzeug.security import generate_password_hash
        from datetime import datetime, timedelta
        try:
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

                # Cria o paciente para teste de Recall IA
                eight_months_ago = datetime.utcnow() - timedelta(days=240)
                p1 = Patient(
                    name="Carlos Eduardo", 
                    phone="11999999999", 
                    last_visit=eight_months_ago, 
                    clinic_id=demo_clinic.id
                )
                db.session.add(p1)
                
                db.session.commit()
                return "✅ BANCO POPULADO! Login: admin@odonto.com | Senha: admin123", 200
            return "ℹ️ O banco já possui os dados da demonstração.", 200
        except Exception as e:
            db.session.rollback()
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