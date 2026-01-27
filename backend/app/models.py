from . import db
from datetime import datetime

# 1. A CLÍNICA
class Clinic(db.Model):
    __tablename__ = 'clinics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cnpj_cpf = db.Column(db.String(20), unique=True)
    plan_type = db.Column(db.String(20), default='trial')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', backref='clinic', lazy=True)
    patients = db.relationship('Patient', backref='clinic', lazy=True)
    inventory_items = db.relationship('InventoryItem', backref='clinic', lazy=True)
    leads = db.relationship('Lead', backref='clinic', lazy=True)
    appointments = db.relationship('Appointment', backref='clinic', lazy=True)
    transactions = db.relationship('Transaction', backref='clinic', lazy=True)

# 2. USUÁRIOS
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='dentist') 
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)

# 3. PACIENTES
class Patient(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
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
    unit = db.Column(db.String(20))
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)

# 5. MARKETING / LEADS
class Lead(db.Model):
    __tablename__ = 'leads'
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    source = db.Column(db.String(50))
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

# 6. AGENDA (CONSULTAS) - NOVO!
class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    
    # Detalhes
    date_time = db.Column(db.DateTime, nullable=False)
    service = db.Column(db.String(200)) # Ex: Limpeza
    duration = db.Column(db.Integer, default=30) # Minutos
    status = db.Column(db.String(20), default='agendado') # agendado, confirmado, concluido, cancelado
    
    # Financeiro da Consulta
    price = db.Column(db.Float, default=0.0)
    is_paid = db.Column(db.Boolean, default=False)

    # Relacionamentos
    patient = db.relationship('Patient', backref='appointments')

# 7. FINANCEIRO (TRANSAÇÕES) - NOVO!
class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)
    
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False) # Valor
    type = db.Column(db.String(20), nullable=False) # 'income' (entrada) ou 'expense' (saida)
    category = db.Column(db.String(50)) # Ex: Tratamento, Aluguel
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Link: Se essa grana veio de uma consulta, a gente amarra aqui!
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)