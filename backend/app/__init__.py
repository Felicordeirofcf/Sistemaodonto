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
    # Configura o Flask para servir arquivos estáticos da pasta 'static'
    app = Flask(__name__, static_folder='static', static_url_path='')

    # --- CONFIGURAÇÃO INTELIGENTE DO BANCO DE DADOS ---
    database_url = os.environ.get('DATABASE_URL')
    
    # Correção para o Render (postgres:// -> postgresql://)
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

    # Importa os Modelos
    from .models import Clinic, User, Patient, InventoryItem, Lead

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

    from .routes.marketing_routes import marketing_bp
    app.register_blueprint(marketing_bp, url_prefix='/api')

    # --- ROTEAMENTO SPA (FRONTEND REACT) ---
    
    # CORREÇÃO AQUI: Mudamos o nome da função de 'serve' para 'index'
    # Isso evita o conflito "overwriting existing endpoint"
    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    # Rota de Emergência para criar tabelas no banco
    @app.route('/api/setup_db')
    def setup_db():
        try:
            with app.app_context():
                db.create_all()
                return jsonify({'message': 'Banco de dados atualizado e tabelas criadas com sucesso!'})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # Tratamento de Erro 404
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api') or request.path.startswith('/auth'):
            return jsonify({'error': 'Not found'}), 404
        return app.send_static_file('index.html')

    return app