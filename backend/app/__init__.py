from flask import Flask, jsonify
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
    # Configura o Flask para saber que os arquivos do site (React) estarão na pasta 'static'
    app = Flask(__name__, static_folder='static', static_url_path='')

    # --- CONFIGURAÇÕES ---
    # Usa o banco de dados SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///odonto_saas.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Chave secreta para criptografar os tokens (Em produção real, use variáveis de ambiente)
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'super-secreta-mudar-em-producao')

    # Inicializa plugins
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # --- TRATAMENTO DE ERROS DO JWT (TOKEN) ---
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'message': 'Token inválido ou corrompido.',
            'error': 'invalid_token'
        }), 422

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'message': 'Token não encontrado.',
            'error': 'authorization_required'
        }), 401
        
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'message': 'O token expirou. Faça login novamente.',
            'error': 'token_expired'
        }), 401
    # ------------------------------------------

    # Importa os modelos para o Flask reconhecer as tabelas
    from .models import Clinic, User, Patient, InventoryItem

    # --- REGISTRO DE ROTAS (BLUEPRINTS) ---
    
    # 1. Autenticação (Login/Cadastro)
    from .routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # 2. Pacientes
    from .routes.patient_routes import patient_bp
    app.register_blueprint(patient_bp, url_prefix='/api')
    
    # 3. Estoque
    from .routes.stock_routes import stock_bp
    app.register_blueprint(stock_bp, url_prefix='/api')

    # 4. Dashboard (Estatísticas)
    from .routes.dashboard_routes import dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/api')

    # 5. AtendeChat AI
    from .routes.atende_chat_routes import atende_chat_bp
    app.register_blueprint(atende_chat_bp, url_prefix='/api')

    # --- ROTEAMENTO DO FRONTEND (REACT) PARA DEPLOY ---
    # Isso é essencial para o Render:
    
    @app.route('/')
    def serve():
        # Entrega o arquivo principal do React
        return app.send_static_file('index.html')

    @app.route('/<path:path>')
    def catch_all(path):
        # Se alguém tentar acessar uma rota da API que não existe, dá erro 404 (JSON)
        if path.startswith('api') or path.startswith('auth'):
            return jsonify({'error': 'Not found'}), 404
        
        # Para qualquer outra rota (ex: /pacientes, /agenda), entrega o React
        # O React Router assume o controle a partir daí
        return app.send_static_file('index.html')

    return app