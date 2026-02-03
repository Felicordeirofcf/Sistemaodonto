from . import db
from datetime import datetime

# =========================================================
# 1) CLÍNICA (CLIENTE SAAS)
# =========================================================
class Clinic(db.Model):
    __tablename__ = "clinics"
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    cnpj_cpf = db.Column(db.String(20), unique=True)

    plan_type = db.Column(db.String(20), default="Bronze")
    max_dentists = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos Core
    users = db.relationship("User", backref="clinic", lazy=True)
    patients = db.relationship("Patient", backref="clinic", lazy=True)
    inventory_items = db.relationship("InventoryItem", backref="clinic", lazy=True)
    appointments = db.relationship("Appointment", backref="clinic", lazy=True)
    transactions = db.relationship("Transaction", backref="clinic", lazy=True)

    # Relacionamentos WhatsApp / Marketing
    whatsapp_connections = db.relationship("WhatsAppConnection", backref="clinic", lazy=True)
    whatsapp_contacts = db.relationship("WhatsAppContact", backref="clinic", lazy=True)
    whatsapp_messages = db.relationship("MessageLog", backref="clinic", lazy=True)
    scheduled_messages = db.relationship("ScheduledMessage", backref="clinic", lazy=True)

    # Relacionamentos CRM e Automação (NOVO)
    crm_stages = db.relationship("CRMStage", backref="clinic", lazy=True)
    crm_cards = db.relationship("CRMCard", backref="clinic", lazy=True)
    automations = db.relationship("AutomacaoRecall", backref="clinic", lazy=True)


# =========================================================
# 2) USUÁRIOS
# =========================================================
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    role = db.Column(db.String(20), default="dentist")
    is_active = db.Column(db.Boolean, default=True)

    clinic_id = db.Column(db.Integer, db.ForeignKey("clinics.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "clinic_id": self.clinic_id,
        }


# =========================================================
# 3) PACIENTES
# =========================================================
class Patient(db.Model):
    __tablename__ = "patients"
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=False)

    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.String(200), nullable=True)

    source = db.Column(db.String(50), default="Manual")
    status = db.Column(db.String(20), default="ativo")

    odontogram_data = db.Column(db.JSON, nullable=True)

    last_visit = db.Column(db.DateTime, default=datetime.utcnow)

    clinic_id = db.Column(db.Integer, db.ForeignKey("clinics.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Paciente pode ter vários contatos whatsapp associados
    whatsapp_contacts = db.relationship("WhatsAppContact", backref="patient", lazy=True)
    
    # Relacionamento com CRM
    crm_cards = db.relationship("CRMCard", backref="patient", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "cpf": self.cpf,
            "email": self.email,
            "address": self.address,
            "status": self.status
        }


# =========================================================
# 4) ESTOQUE
# =========================================================
class InventoryItem(db.Model):
    __tablename__ = "inventory_items"
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    
    category = db.Column(db.String(50), default="Material") 
    
    quantity = db.Column(db.Float, default=0.0)
    min_quantity = db.Column(db.Float, default=5.0) 
    
    purchase_price = db.Column(db.Float, default=0.0) 

    unit = db.Column(db.String(20), default="unidade")

    clinic_id = db.Column(db.Integer, db.ForeignKey("clinics.id"), nullable=False)


# =========================================================
# 5) AGENDA
# =========================================================
class Appointment(db.Model):
    __tablename__ = "appointments"
    id = db.Column(db.Integer, primary_key=True)

    date_time = db.Column(db.DateTime, nullable=False)

    patient_name = db.Column(db.String(100))
    procedure = db.Column(db.String(100))
    status = db.Column(db.String(20), default="confirmed")

    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey("clinics.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date_time.isoformat(),
            "patient_name": self.patient_name,
            "procedure": self.procedure,
            "status": self.status
        }


# =========================================================
# 6) FINANCEIRO
# =========================================================
class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)

    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)

    type = db.Column(db.String(20), nullable=False)  # income | expense
    category = db.Column(db.String(50), default="Outros")

    date = db.Column(db.DateTime, default=datetime.utcnow)

    clinic_id = db.Column(db.Integer, db.ForeignKey("clinics.id"), nullable=False)


# =========================================================
# 7) WHATSAPP / MARKETING
# =========================================================

class WhatsAppConnection(db.Model):
    __tablename__ = "whatsapp_connections"
    id = db.Column(db.Integer, primary_key=True)

    clinic_id = db.Column(db.Integer, db.ForeignKey("clinics.id"), nullable=False, index=True)

    provider = db.Column(db.String(20), nullable=False, default="qr")  # qr | cloud (futuro)
    status = db.Column(db.String(20), nullable=False, default="disconnected")  # connected|connecting|disconnected

    session_data = db.Column(db.JSON, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WhatsAppContact(db.Model):
    __tablename__ = "whatsapp_contacts"
    id = db.Column(db.Integer, primary_key=True)

    clinic_id = db.Column(db.Integer, db.ForeignKey("clinics.id"), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=True, index=True)

    phone = db.Column(db.String(32), nullable=False, index=True)
    name = db.Column(db.String(120), nullable=True)

    opt_in = db.Column(db.Boolean, default=True)
    opt_out_at = db.Column(db.DateTime, nullable=True)

    last_inbound_at = db.Column(db.DateTime, nullable=True)
    last_outbound_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("clinic_id", "phone", name="uq_whatsapp_contact_clinic_phone"),
    )


class MessageLog(db.Model):
    __tablename__ = "whatsapp_message_logs"
    id = db.Column(db.Integer, primary_key=True)

    clinic_id = db.Column(db.Integer, db.ForeignKey("clinics.id"), nullable=False, index=True)
    contact_id = db.Column(db.Integer, db.ForeignKey("whatsapp_contacts.id"), nullable=True, index=True)

    direction = db.Column(db.String(10), nullable=False)  # in | out
    body = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(20), nullable=False, default="queued")  # queued|sent|failed|delivered|read
    provider_message_id = db.Column(db.String(120), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    contact = db.relationship("WhatsAppContact", backref=db.backref("messages", lazy=True))


class ScheduledMessage(db.Model):
    __tablename__ = "scheduled_messages"
    id = db.Column(db.Integer, primary_key=True)

    clinic_id = db.Column(db.Integer, db.ForeignKey("clinics.id"), nullable=False, index=True)
    contact_id = db.Column(db.Integer, db.ForeignKey("whatsapp_contacts.id"), nullable=False, index=True)

    type = db.Column(db.String(50), nullable=False)  # followup_30d | reminder_24h | etc
    payload = db.Column(db.JSON, nullable=False)

    run_at = db.Column(db.DateTime, nullable=False, index=True)

    status = db.Column(db.String(20), nullable=False, default="pending")  # pending|sent|skipped|failed
    fail_reason = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    contact = db.relationship("WhatsAppContact", backref=db.backref("scheduled", lazy=True))


# =========================================================
# 8) CRM & AUTOMAÇÃO (NOVOS)
# =========================================================

class AutomacaoRecall(db.Model):
    __tablename__ = 'automacoes_recall'
    
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)
    
    nome = db.Column(db.String(100)) # Ex: "Recall 6 Meses"
    dias_ausente = db.Column(db.Integer) # Ex: 180
    horario_disparo = db.Column(db.String(5)) # Ex: "09:00"
    
    mensagem_template = db.Column(db.Text) # "Olá {nome}..."
    ativo = db.Column(db.Boolean, default=True)


class CRMStage(db.Model):
    __tablename__ = 'crm_stages'
    
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)
    
    nome = db.Column(db.String(50)) # Ex: "A Contactar"
    ordem = db.Column(db.Integer)   # 1, 2, 3
    cor = db.Column(db.String(7))   # #FF0000
    
    is_initial = db.Column(db.Boolean, default=False)
    is_success = db.Column(db.Boolean, default=False)


class CRMCard(db.Model):
    __tablename__ = 'crm_cards'
    
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)
    
    paciente_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    stage_id = db.Column(db.Integer, db.ForeignKey('crm_stages.id'))
    
    ultima_interacao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='open') # open, won, lost
    
    # Relacionamentos
    history = db.relationship("CRMHistory", backref="card", lazy=True)
    stage = db.relationship("CRMStage", backref="cards", lazy=True)


class CRMHistory(db.Model):
    __tablename__ = 'crm_history'
    
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('crm_cards.id'))
    
    tipo = db.Column(db.String(50)) # BOT_SENT, STAGE_CHANGE
    descricao = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)