from . import db
from datetime import datetime

# 1. A CLÍNICA (O CLIENTE PAGANTE)
class Clinic(db.Model):
    __tablename__ = 'clinics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cnpj_cpf = db.Column(db.String(20), unique=True)
    plan_type = db.Column(db.String(20), default='pro') # trial, pro, elite
    # CORREÇÃO: Adicionada a coluna is_active para evitar erro no login
    is_active = db.Column(db.Boolean, default=True) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    users = db.relationship('User', backref='clinic', lazy=True)
    patients = db.relationship('Patient', backref='clinic', lazy=True)
    inventory_items = db.relationship('InventoryItem', backref='clinic', lazy=True)
    leads = db.relationship('Lead', backref='clinic', lazy=True)
    appointments = db.relationship('Appointment', backref='clinic', lazy=True)
    transactions = db.relationship('Transaction', backref='clinic', lazy=True)

# 2. OS USUÁRIOS (DENTISTAS/SECRETÁRIAS)
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='dentist') # admin, dentist, secretary
    
    # VÍNCULO SAAS: Todo usuário pertence a uma clínica
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)

# 3. PACIENTES
class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    # Odontograma Digital (Salva o JSON do estado dos dentes)
    odontogram_data = db.Column(db.JSON, nullable=True) 
    last_visit = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='ativo')
    
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)

# 4. ESTOQUE
class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=0)
    min_quantity = db.Column(db.Integer, default=5)
    unit = db.Column(db.String(20)) # cx, un, ml
    
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)

# 5. MARKETING / LEADS (CRM)
class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    source = db.Column(db.String(50)) # Ex: 'Instagram', 'Google'
    status = db.Column(db.String(50), default='new') 
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'source': self.source,
            'status': self.status,
            'notes': self.notes
        }

# 6. AGENDA (CONSULTAS)
class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    
    date_time = db.Column(db.DateTime, nullable=False)
    service = db.Column(db.String(200)) 
    status = db.Column(db.String(20), default='agendado') # agendado, confirmado, concluido, cancelado
    price = db.Column(db.Float, default=0.0)
    is_paid = db.Column(db.Boolean, default=False)

    # Relacionamento para acessar dados do paciente na agenda
    patient = db.relationship('Patient', backref='appointments_list')

# 7. FINANCEIRO PROFISSIONAL
class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)
    
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False) # Valor bruto
    cost = db.Column(db.Float, default=0.0)      # Custos associados
    type = db.Column(db.String(20), nullable=False) # 'income' ou 'expense'
    category = db.Column(db.String(50)) # Ex: Tratamento, Aluguel, Material
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)