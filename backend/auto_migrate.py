from app import create_app, db
import time

app = create_app()

def init_db():
    with app.app_context():
        print("🔄 Aguardando conexão com o banco...")
        # Pequeno delay para garantir que o banco subiu
        time.sleep(2) 
        
        print("🔄 Verificando e criando tabelas...")
        try:
            # O db.create_all() cria apenas o que NÃO existe.
            # Ele não apaga dados existentes.
            db.create_all()
            print("✅ Banco de Dados sincronizado com sucesso!")
        except Exception as e:
            print(f"❌ Erro crítico na migração: {e}")

if __name__ == "__main__":
    init_db()