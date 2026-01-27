from . import db
from datetime import datetime

# 1. A CLÍNICA (O CLIENTE PAGANTE)
class Clinic(db.Model):
    __tablename__ = 'clinics'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cnpj_cpf = db.Column(db.String(20), unique=True)
    plan_type = db.Column(db.String(20), default='trial') # trial, pro, elite
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos (Para o Python saber navegar)
    users = db.relationship('User', backref='clinic', lazy=True)
    patients = db.relationship('Patient', backref='clinic', lazy=True)
    inventory_items = db.relationship('InventoryItem', backref='clinic', lazy=True)
    # NOVO: Relacionamento com Leads
    leads = db.relationship('Lead', backref='clinic', lazy=True)

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
    
    # Odontograma Digital (Salva o JSON inteiro do React aqui!)
    odontogram_data = db.Column(db.JSON, nullable=True) 
    
    last_visit = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='ativo')
    
    # VÍNCULO SAAS: Paciente pertence a uma clínica
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)

# 4. ESTOQUE
class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=0)
    min_quantity = db.Column(db.Integer, default=5) # Para alerta de estoque baixo
    unit = db.Column(db.String(20)) # cx, un, ml
    
    # VÍNCULO SAAS
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)

# 5. MARKETING / LEADS (CRM)
class Lead(db.Model):
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    source = db.Column(db.String(50)) # Ex: 'Instagram', 'Google'
    status = db.Column(db.String(50), default='new') # 'new', 'contacted', 'scheduled', 'treating'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'source': self.source,
            'status': self.status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }