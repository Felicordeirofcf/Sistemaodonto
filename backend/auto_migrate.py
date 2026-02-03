import sys
import os
from sqlalchemy import text

# Adiciona o diretório atual ao path para o Python achar a pasta 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

app = create_app()

def init_db():
    with app.app_context():
        print("🔄 Sincronizando Banco de Dados Odontológico...")
        try:
            # 1. Tenta criar tabelas que não existem
            db.create_all()
            
            # 2. Força a criação de colunas específicas que podem estar faltando no PostgreSQL (Render)
            # O db.create_all() não adiciona colunas em tabelas já existentes.
            print("🛠️ Verificando colunas extras em crm_cards...")
            
            alter_statements = [
                "ALTER TABLE crm_cards ADD COLUMN IF NOT EXISTS paciente_nome VARCHAR(100);",
                "ALTER TABLE crm_cards ADD COLUMN IF NOT EXISTS paciente_phone VARCHAR(30);",
                "ALTER TABLE crm_cards ADD COLUMN IF NOT EXISTS historico_conversas TEXT;",
                "ALTER TABLE crm_cards ADD COLUMN IF NOT EXISTS valor_proposta FLOAT DEFAULT 0.0;"
            ]
            
            for statement in alter_statements:
                try:
                    db.session.execute(text(statement))
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    print(f"⚠️ Aviso ao executar '{statement}': {e}")

            print("✅ Sincronização concluída!")
        except Exception as e:
            print(f"❌ Erro crítico na migração: {e}")

if __name__ == "__main__":
    init_db()
