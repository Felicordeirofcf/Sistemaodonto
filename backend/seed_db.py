import os
from app import create_app, db
from app.models import Clinic, User, Patient, Lead, InventoryItem, CRMStage, CRMCard
from werkzeug.security import generate_password_hash
from sqlalchemy import inspect
from datetime import datetime

app = create_app()

def seed():
    with app.app_context():
        print("🚀 Iniciando limpeza e população do banco...")
        
        db.drop_all()
        db.create_all()

        mapper = inspect(User)
        columns = [column.key for column in mapper.attrs]
        name_field = 'name' if 'name' in columns else 'user_name'

        # 1. CLÍNICA (SaaS)
        demo_clinic = Clinic(
            name="OdontoSys Premium Demo",
            plan_type="Ouro",
            max_dentists=10,
            is_active=True
        )
        db.session.add(demo_clinic)
        db.session.flush()

        # 2. USUÁRIO ADMINISTRADOR
        admin_pwd = generate_password_hash("admin123")
        user_data = {
            name_field: "Dr. Ricardo (Admin)",
            "email": "admin@odonto.com",
            "password_hash": admin_pwd,
            "role": "admin",
            "is_active": True,
            "clinic_id": demo_clinic.id
        }
        admin = User(**user_data)
        db.session.add(admin)

        # 3. PACIENTES
        pacientes = [
            Patient(name="Carlos Eduardo", email="carlos@email.com", phone="11999999999", clinic_id=demo_clinic.id),
            Patient(name="Mariana Souza", email="mariana@email.com", phone="11888888888", clinic_id=demo_clinic.id),
            Patient(name="Roberto Lima", email="roberto@email.com", phone="11777777777", clinic_id=demo_clinic.id)
        ]
        db.session.add_all(pacientes)

        # 4. LEADS
        leads = [
            Lead(name="Joana Silva", source="Instagram", status="novo", phone="11911111111", clinic_id=demo_clinic.id),
            Lead(name="Pedro Rocha", source="Google Ads", status="novo", phone="11922222222", clinic_id=demo_clinic.id)
        ]
        db.session.add_all(leads)
        db.session.flush()

        # 5. CRM STAGES & CARDS
        stage_novo = CRMStage(clinic_id=demo_clinic.id, nome="Novo Lead", cor="yellow", ordem=0, is_initial=True)
        db.session.add(stage_novo)
        db.session.flush()

        card1 = CRMCard(
            clinic_id=demo_clinic.id,
            stage_id=stage_novo.id,
            paciente_nome="Joana Silva",
            paciente_phone="11911111111",
            historico_conversas="Lead vindo do Instagram",
            status="open",
            ultima_interacao=datetime.utcnow()
        )
        db.session.add(card1)
        
        # 6. ESTOQUE
        itens = [
            InventoryItem(name="Luva Nitrílica", quantity=50, min_quantity=10, unit="par", clinic_id=demo_clinic.id),
            InventoryItem(name="Resina A2", quantity=10, min_quantity=2, unit="tubo", clinic_id=demo_clinic.id),
            InventoryItem(name="Anestésico", quantity=100, min_quantity=20, unit="tubete", clinic_id=demo_clinic.id)
        ]
        db.session.add_all(itens)

        try:
            db.session.commit()
            print("\n✅ BANCO POPULADO COM SUCESSO!")
            print(f"🔑 Login: admin@odonto.com | Senha: admin123")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro crítico no commit: {str(e)}")

if __name__ == "__main__":
    seed()
