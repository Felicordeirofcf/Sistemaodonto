import os
from app import create_app, db
from app.models import Clinic, User, Patient, Lead, InventoryItem
from werkzeug.security import generate_password_hash
from sqlalchemy import inspect

app = create_app()

def seed():
    with app.app_context():
        print("🚀 Recriando tabelas...")
        db.drop_all()
        db.create_all()

        # DEPURAÇÃO: Descobrir o nome real da coluna
        mapper = inspect(User)
        columns = [column.key for column in mapper.attrs]
        print(f"🔍 Colunas detectadas na tabela User: {columns}")

        # Busca qual dessas colunas parece ser a de 'nome'
        possible_names = ['name', 'full_name', 'user_name', 'username', 'display_name']
        name_field = next((f for f in possible_names if f in columns), None)
        
        if not name_field:
            print("❌ Erro: Não identifiquei a coluna de nome. Verifique seu models.py")
            return

        print(f"ℹ️ Usando o campo identificado: '{name_field}'")

        # 1. CLÍNICA
        demo_clinic = Clinic(
            name="OdontoSys Premium Demo",
            plan_type="Ouro",
            max_dentists=10,
            is_active=True
        )
        db.session.add(demo_clinic)
        db.session.flush()

        # 2. USUÁRIOS (Usando o campo detectado)
        admin_pwd = generate_password_hash("admin123")
        
        admin = User(**{
            name_field: "Dr. Ricardo (Admin)",
            "email": "admin@odonto.com",
            "password_hash": admin_pwd,
            "role": "admin",
            "clinic_id": demo_clinic.id
        })
        db.session.add(admin)

        # 3. PACIENTES
        pacientes = [
            Patient(name="Carlos Eduardo", email="carlos@email.com", phone="11999999999", clinic_id=demo_clinic.id),
            Patient(name="Mariana Souza", email="mariana@email.com", phone="11888888888", clinic_id=demo_clinic.id)
        ]
        db.session.add_all(pacientes)

        # 4. LEADS (CRM)
        leads = [
            Lead(name="Joana Silva", source="Instagram", status="new", phone="11911111111", clinic_id=demo_clinic.id),
            Lead(name="Pedro Rocha", source="Google Ads", status="contacted", phone="11922222222", clinic_id=demo_clinic.id)
        ]
        db.session.add_all(leads)

        try:
            db.session.commit()
            print("\n✅ Sucesso! Banco populado.")
            print(f"🔑 Login: admin@odonto.com | Senha: admin123")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro no commit: {str(e)}")

if __name__ == "__main__":
    seed()