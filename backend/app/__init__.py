from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os

# Inicializa as extensões globalmente
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    # Configura o Flask para servir arquivos estáticos (Frontend Build)
    app = Flask(__name__, static_folder='static', static_url_path='')

    # --- CONFIGURAÇÃO DO BANCO DE DADOS ---
    database_url = os.environ.get('DATABASE_URL')
    
    # Correção obrigatória para o Render (postgres:// -> postgresql://)
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///odonto_saas.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secreta-mudar-em-producao')

    # Inicializa plugins
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Importa os Modelos ANTES dos Blueprints para evitar problemas de dependência circular
    from .models import Clinic, User, Patient, InventoryItem, Lead, Appointment, Transaction, Procedure

    # --- HANDLERS DE TOKEN JWT ---
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'message': 'Token inválido.', 'error': 'invalid_token'}), 422

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'message': 'Token não encontrado.', 'error': 'authorization_required'}), 401
        
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'message': 'Token expirado.', 'error': 'token_expired'}), 401

    # --- REGISTRO DE BLUEPRINTS ---
    # 1. Autenticação (Login, Status)
    from .routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # 2. API Principal (Pacientes, Estoque, Dashboard, Equipe, etc)
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
    app.register_blueprint(team_bp, url_prefix='/api') # Rota de Gestão de Equipe

    from .routes.procedure_routes import procedure_bp
    app.register_blueprint(procedure_bp, url_prefix='/api') # Rota de Fichas Técnicas

    # --- ROTAS DE UTILIDADE & NAVEGAÇÃO ---

    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    @app.route('/api/setup_db')
    def setup_db():
        """Cria tabelas faltantes e garante a nova coluna max_dentists"""
        try:
            db.create_all()
            return jsonify({'message': 'Banco de dados sincronizado com sucesso!'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/danger_reset_db')
    def danger_reset_db():
        """APAGA TUDO e recria o banco (Cuidado!)"""
        confirm = request.args.get('confirm')
        if confirm != 'true':
            return jsonify({'error': 'Adicione ?confirm=true para resetar o banco'}), 403
            
        try:
            db.drop_all()
            db.create_all()
            return jsonify({'message': 'BANCO RESETADO TOTALMENTE. Todas as colunas novas foram criadas.'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Fallback para o React (SPA)
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api') or request.path.startswith('/auth'):
            return jsonify({'error': 'Rota de API não encontrada'}), 404
        return app.send_static_file('index.html')

    return app