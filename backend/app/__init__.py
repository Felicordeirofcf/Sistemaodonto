from flask import Flask, jsonify, request # <--- IMPORTANTE: Adicionei 'request' aqui
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
    # Configura o Flask para servir arquivos estáticos da pasta 'static'
    app = Flask(__name__, static_folder='static', static_url_path='')

    # Configuração do Banco e JWT
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///odonto_saas.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secreta-mudar-em-producao')

    # Inicializa plugins
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # --- TRATAMENTO DE ERROS DO JWT ---
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'message': 'Token inválido.', 'error': 'invalid_token'}), 422

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'message': 'Token não encontrado.', 'error': 'authorization_required'}), 401
        
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'message': 'Token expirado.', 'error': 'token_expired'}), 401

    # Importa Modelos
    from .models import Clinic, User, Patient, InventoryItem

    # --- REGISTRO DE ROTAS DA API ---
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

    # --- SOLUÇÃO DEFINITIVA PARA O ERRO 404 (ROTEAMENTO SPA) ---
    
    # 1. Rota Raiz (Carrega o site)
    @app.route('/')
    def serve():
        return app.send_static_file('index.html')

    # 2. Tratamento de Erro 404 (Salva o Refresh da página)
    # Se o Flask não achar a rota (ex: /login, /agenda), ele cai aqui.
    @app.errorhandler(404)
    def not_found(e):
        # Se for uma tentativa de acessar a API que não existe, retorna JSON de erro mesmo
        if request.path.startswith('/api') or request.path.startswith('/auth'):
            return jsonify({'error': 'Not found'}), 404
        
        # Se for qualquer outra coisa (rota do navegador), entrega o React
        return app.send_static_file('index.html')

    return app