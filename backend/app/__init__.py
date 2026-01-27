from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os

# Inicializa as extensões
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__, static_folder='static', static_url_path='')

    # --- CONFIGURAÇÃO INTELIGENTE DO BANCO DE DADOS ---
    # 1. Tenta pegar a URL do banco do ambiente (Render)
    database_url = os.environ.get('DATABASE_URL')
    
    # 2. Correção para o Render (ele usa 'postgres://' mas o SQLAlchemy quer 'postgresql://')
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    # 3. Se tiver URL (Nuvem), usa Postgres. Se não (Local), usa SQLite.
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///odonto_saas.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secreta-mudar-em-producao')

    # Inicializa plugins
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # --- HANDLERS DE TOKEN ---
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'message': 'Token inválido.', 'error': 'invalid_token'}), 422

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'message': 'Token não encontrado.', 'error': 'authorization_required'}), 401
        
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'message': 'Token expirado.', 'error': 'token_expired'}), 401

    # Modelos e Rotas
    from .models import Clinic, User, Patient, InventoryItem

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

    # Roteamento SPA (Frontend)
    @app.route('/')
    def serve():
        return app.send_static_file('index.html')

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api') or request.path.startswith('/auth'):
            return jsonify({'error': 'Not found'}), 404
        return app.send_static_file('index.html')

    return app