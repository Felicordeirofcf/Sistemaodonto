import os
from app import create_app, db
from app.models import Clinic, User, Patient, Lead, InventoryItem
from werkzeug.security import generate_password_hash
from sqlalchemy import inspect

app = create_app()

def seed():
    with app.app_context():
        print("🚀 Iniciando limpeza e população do banco...")
        
        # O drop_all/create_all garante que as novas colunas como 'is_active' existam
        db.drop_all()
        db.create_all()

        # DEPURAÇÃO: Identifica as colunas reais para evitar o erro UndefinedColumn
        mapper = inspect(User)
        columns = [column.key for column in mapper.attrs]
        print(f"🔍 Colunas detectadas na tabela User: {columns}")

        # O seu banco usa 'name' conforme revisamos no models.py
        name_field = 'name' if 'name' in columns else 'user_name'
        print(f"ℹ️ Usando o campo de nome: '{name_field}'")

        # 1. CLÍNICA (SaaS)
        demo_clinic = Clinic(
            name="OdontoSys Premium Demo",
            plan_type="Ouro", # Plano configurado para liberar 10 dentistas
            max_dentists=10,
            is_active=True # Essencial para não cair na tela de BloqueioPagamento
        )
        db.session.add(demo_clinic)
        db.session.flush()

        # 2. USUÁRIO ADMINISTRADOR (Ricardo)
        admin_pwd = generate_password_hash("admin123")
        
        user_data = {
            name_field: "Dr. Ricardo (Admin)",
            "email": "admin@odonto.com",
            "password_hash": admin_pwd,
            "role": "admin",
            "is_active": True, # Garante que a rota /auth/status retorne True
            "clinic_id": demo_clinic.id
        }
        
        admin = User(**user_data)
        db.session.add(admin)

        # 3. PACIENTES (Para testar o Odontograma)
        pacientes = [
            Patient(name="Carlos Eduardo", email="carlos@email.com", phone="11999999999", clinic_id=demo_clinic.id),
            Patient(name="Mariana Souza", email="mariana@email.com", phone="11888888888", clinic_id=demo_clinic.id),
            Patient(name="Roberto Lima", email="roberto@email.com", phone="11777777777", clinic_id=demo_clinic.id)
        ]
        db.session.add_all(pacientes)

        # 4. LEADS (Para o CRM Kanban)
        leads = [
            Lead(name="Joana Silva", source="Instagram", status="new", phone="11911111111", clinic_id=demo_clinic.id),
            Lead(name="Pedro Rocha", source="Google Ads", status="contacted", phone="11922222222", clinic_id=demo_clinic.id)
        ]
        db.session.add_all(leads)
        
        # 5. ESTOQUE (Para a Ficha Técnica)
        itens = [
            InventoryItem(name="Luva Nitrílica", quantity=50, min_stock=10, unit="par", clinic_id=demo_clinic.id),
            InventoryItem(name="Resina A2", quantity=10, min_stock=2, unit="tubo", clinic_id=demo_clinic.id),
            InventoryItem(name="Anestésico", quantity=100, min_stock=20, unit="tubete", clinic_id=demo_clinic.id)
        ]
        db.session.add_all(itens)

        try:
            db.session.commit()
            print("\n✅ BANCO POPULADO COM SUCESSO!")
            print(f"🔑 Login: admin@odonto.com | Senha: admin123")
            print(f"📊 Clínica: {demo_clinic.name} (ID: {demo_clinic.id})")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro crítico no commit: {str(e)}")

if __name__ == "__main__":
    seed()