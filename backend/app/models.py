from . import db
from datetime import datetime

# 1. A CLÍNICA (CLIENTE SAAS)
class Clinic(db.Model):
    __tablename__ = 'clinics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cnpj_cpf = db.Column(db.String(20), unique=True)
    plan_type = db.Column(db.String(20), default='Bronze')
    max_dentists = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    users = db.relationship('User', backref='clinic', lazy=True)
    patients = db.relationship('Patient', backref='clinic', lazy=True)
    inventory_items = db.relationship('InventoryItem', backref='clinic', lazy=True)
    appointments = db.relationship('Appointment', backref='clinic', lazy=True)
    transactions = db.relationship('Transaction', backref='clinic', lazy=True)

# 2. USUÁRIOS (Logins do Sistema)
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) 
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='dentist')
    is_active = db.Column(db.Boolean, default=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "clinic_id": self.clinic_id
        }

# 3. PACIENTES
class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    source = db.Column(db.String(50), default='Manual')
    status = db.Column(db.String(20), default='ativo') 
    odontogram_data = db.Column(db.JSON, nullable=True)
    
    last_visit = db.Column(db.DateTime, default=datetime.utcnow) 
    
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 4. ESTOQUE (Itens de Consumo)
class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, default=0.0)
    min_stock = db.Column(db.Float, default=5.0) 
    unit = db.Column(db.String(20), default='unidade')
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)

# 5. AGENDA
class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.DateTime, nullable=False)
    patient_name = db.Column(db.String(100)) 
    procedure = db.Column(db.String(100))
    status = db.Column(db.String(20), default='confirmed')
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)

# 6. FINANCEIRO (Receitas e Despesas)
class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False) # 'income' ou 'expense'
    category = db.Column(db.String(50), default='Outros')
    date = db.Column(db.DateTime, default=datetime.utcnow)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)
