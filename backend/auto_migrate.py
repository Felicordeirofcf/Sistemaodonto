import sys
import os

# Adiciona o diretório atual ao path para o Python achar a pasta 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
import time

app = create_app()

def init_db():
    with app.app_context():
        print("🔄 Sincronizando Banco de Dados Odontológico...")
        try:
            db.create_all()
            print("✅ Tabelas (Agenda, Leads, Financeiro) verificadas!")
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    init_db()