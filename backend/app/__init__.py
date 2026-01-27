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
    # Configura o Flask para servir arquivos estáticos da pasta 'static' (onde o React build fica)
    app = Flask(__name__, static_folder='static', static_url_path='')

    # --- CONFIGURAÇÃO INTELIGENTE DO BANCO DE DADOS ---
    # 1. Tenta pegar a URL do banco do ambiente (Render)
    database_url = os.environ.get('DATABASE_URL')
    
    # 2. Correção para o Render (ele usa 'postgres://' mas o SQLAlchemy exige 'postgresql://')
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

    # --- HANDLERS DE TOKEN (MENSAGENS DE ERRO JSON) ---
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'message': 'Token inválido.', 'error': 'invalid_token'}), 422

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'message': 'Token não encontrado.', 'error': 'authorization_required'}), 401
        
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'message': 'Token expirado.', 'error': 'token_expired'}), 401

    # Importa os Modelos (dentro da função para evitar ciclo de importação)
    from .models import Clinic, User, Patient, InventoryItem

    # --- REGISTRO DE ROTAS (BLUEPRINTS) ---
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

    # --- ROTEAMENTO SPA (FRONTEND REACT) ---
    # 1. Rota Raiz: Entrega o index.html do React
    @app.route('/')
    def serve():
        return app.send_static_file('index.html')

    # 2. Tratamento de Erro 404:
    # Se o navegador pedir uma rota que o Flask não conhece (ex: /agenda), 
    # entregamos o index.html para o React Router assumir.
    # Se for uma API (/api/...), retornamos erro 404 JSON real.
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api') or request.path.startswith('/auth'):
            return jsonify({'error': 'Not found'}), 404
        return app.send_static_file('index.html')
    # --- ROTEAMENTO SPA (FRONTEND REACT) ---
    @app.route('/')
    def serve():
        return app.send_static_file('index.html')

    # ===> ADICIONE ESTE BLOCO AQUI (ROTA DE EMERGÊNCIA) <===
    @app.route('/api/setup_db')
    def setup_db():
        try:
            with app.app_context():
                # Força a criação de todas as tabelas que estão nos Models mas não no Banco
                db.create_all()
                return jsonify({'message': 'Banco de dados atualizado e tabelas criadas com sucesso!'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    # ========================================================

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api') or request.path.startswith('/auth'):
            return jsonify({'error': 'Not found'}), 404
        return app.send_static_file('index.html')
    
    from .routes.marketing_routes import marketing_bp
    app.register_blueprint(marketing_bp, url_prefix='/api')

    return app