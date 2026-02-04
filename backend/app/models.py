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

    # ✅ CAMPO ESSENCIAL: Número oficial para redirecionamento (Ex: 5521987708652)
    whatsapp_number = db.Column(db.String(20), nullable=True) 

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

    # Relacionamentos WhatsApp / Marketing Core
    whatsapp_connections = db.relationship("WhatsAppConnection", backref="clinic", lazy=True)
    whatsapp_contacts = db.relationship("WhatsAppContact", backref="clinic", lazy=True)
    whatsapp_messages = db.relationship("MessageLog", backref="clinic", lazy=True)
    scheduled_messages = db.relationship("ScheduledMessage", backref="clinic", lazy=True)

    # Relacionamentos CRM e Automação
    crm_stages = db.relationship("CRMStage", backref="clinic", lazy=True)
    crm_cards = db.relationship("CRMCard", backref="clinic", lazy=True)
    automations = db.relationship("AutomacaoRecall", backref="clinic", lazy=True)

    # Relacionamentos Marketing (Campanhas e Leads)
    marketing_campaigns = db.relationship("Campaign", backref="clinic", lazy=True)
    marketing_leads = db.relationship("Lead", backref="clinic", lazy=True)


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

    receive_marketing = db.Column(db.Boolean, default=True) 

    clinic_id = db.Column(db.Integer, db.ForeignKey("clinics.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    whatsapp_contacts = db.relationship("WhatsAppContact", backref="patient", lazy=True)
    crm_cards = db.relationship("CRMCard", backref="patient", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "cpf": self.cpf,
            "email": self.email,
            "address": self.address,
            "status": self.status,
            "receive_marketing": self.receive_marketing
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

    clinic_id = db.Column(db.Integer, db.ForeignKey("clinics.id"), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=True)
    lead_id = db.Column(db.Integer, db.ForeignKey("marketing_leads.id"), nullable=True)

    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)
    
    status = db.Column(db.String(20), default="scheduled") # scheduled|confirmed|done|cancelled
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Back-compatibility fields (optional, but keeping for safety if used elsewhere)
    @property
    def date_time(self):
        return self.start_datetime
    
    @property
    def patient_name(self):
        if self.patient:
            return self.patient.name
        return self.title

    def to_dict(self):
        return {
            "id": self.id,
            "clinic_id": self.clinic_id,
            "patient_id": self.patient_id,
            "lead_id": self.lead_id,
            "title": self.title,
            "description": self.description,
            "start": self.start_datetime.isoformat(),
            "end": self.end_datetime.isoformat(),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
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
# 7) WHATSAPP / MARKETING CORE
# =========================================================
class WhatsAppConnection(db.Model):
    __tablename__ = "whatsapp_connections"
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey("clinics.id"), nullable=False, index=True)
    
    # ✅ CAMPO ADICIONADO: Nome da instância (Ex: clinica_v3_1)
    instance_name = db.Column(db.String(50), unique=True, index=True) 
    
    provider = db.Column(db.String(20), nullable=False, default="qr")
    status = db.Column(db.String(20), nullable=False, default="disconnected")
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
    status = db.Column(db.String(20), nullable=False, default="queued")
    provider_message_id = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    contact = db.relationship("WhatsAppContact", backref=db.backref("messages", lazy=True))


class ScheduledMessage(db.Model):
    __tablename__ = "scheduled_messages"
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey("clinics.id"), nullable=False, index=True)
    contact_id = db.Column(db.Integer, db.ForeignKey("whatsapp_contacts.id"), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    run_at = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    fail_reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    contact = db.relationship("WhatsAppContact", backref=db.backref("scheduled", lazy=True))


# ✅ NOVA TABELA: Sessões de Chat para Máquina de Estados
class ChatSession(db.Model):
    __tablename__ = "chat_sessions"
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey("clinics.id"), nullable=False, index=True)
    sender_id = db.Column(db.String(100), nullable=False, index=True) # JID ou Phone
    
    state = db.Column(db.String(50), default='start')
    data = db.Column(db.JSON, default={})
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint("clinic_id", "sender_id", name="uq_chat_session_clinic_sender"),
    )


# =========================================================
# 8) CRM & AUTOMAÇÃO
# =========================================================
class AutomacaoRecall(db.Model):
    __tablename__ = 'automacoes_recall'
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)
    nome = db.Column(db.String(100))
    dias_ausente = db.Column(db.Integer)
    horario_disparo = db.Column(db.String(5))
    mensagem_template = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)


class CRMStage(db.Model):
    __tablename__ = 'crm_stages'
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)
    nome = db.Column(db.String(100))
    ordem = db.Column(db.Integer)
    cor = db.Column(db.String(7))
    is_initial = db.Column(db.Boolean, default=False)
    is_success = db.Column(db.Boolean, default=False)


class CRMCard(db.Model):
    __tablename__ = 'crm_cards'
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False)
    
    # ✅ CAMPOS ESSENCIAIS PARA LEADS DO WHATSAPP
    paciente_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)
    paciente_nome = db.Column(db.String(100)) 
    paciente_phone = db.Column(db.String(30)) 
    
    stage_id = db.Column(db.Integer, db.ForeignKey('crm_stages.id'))
    historico_conversas = db.Column(db.Text) 
    valor_proposta = db.Column(db.Float, default=0.0)
    
    ultima_interacao = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='open') # open, won, lost
    
    history = db.relationship("CRMHistory", backref="card", lazy=True)
    stage = db.relationship("CRMStage", backref="cards", lazy=True)


class CRMHistory(db.Model):
    __tablename__ = 'crm_history'
    id = db.Column(db.Integer, primary_key=True)
    card_id = db.Column(db.Integer, db.ForeignKey('crm_cards.id'))
    tipo = db.Column(db.String(50))
    descricao = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)


# =========================================================
# 9) MARKETING AVANÇADO (LEADS & CAMPANHAS)
# =========================================================
class LeadStatus:
    NEW = 'novo'
    IN_CHAT = 'em_atendimento'
    QUALIFIED = 'qualificado'
    SCHEDULED = 'agendado'
    CONVERTED = 'convertido'
    LOST = 'perdido'

class Campaign(db.Model):
    __tablename__ = 'marketing_campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False, index=True)
    
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(50), unique=True, index=True)
    tracking_code = db.Column(db.String(20), unique=True, index=True)
    
    whatsapp_message_template = db.Column(db.Text)
    landing_page_data = db.Column(db.JSON)
    
    clicks_count = db.Column(db.Integer, default=0)
    leads_count = db.Column(db.Integer, default=0)
    
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    leads = db.relationship('Lead', backref='campaign', lazy='dynamic')


class Lead(db.Model):
    __tablename__ = 'marketing_leads'
    
    id = db.Column(db.Integer, primary_key=True)
    clinic_id = db.Column(db.Integer, db.ForeignKey('clinics.id'), nullable=False, index=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('marketing_campaigns.id'), nullable=True)
    
    name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(30), nullable=False, index=True)
    
    status = db.Column(db.String(20), default=LeadStatus.NEW)
    source = db.Column(db.String(50))
    
    chatbot_state = db.Column(db.String(50), default='START') 
    chatbot_data = db.Column(db.JSON, default={})
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Soft Delete
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)


class LeadEvent(db.Model):
    __tablename__ = 'marketing_lead_events'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('marketing_leads.id'), nullable=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('marketing_campaigns.id'), nullable=True)
    
    event_type = db.Column(db.String(50)) # 'click', 'msg_in', 'status_change'
    metadata_json = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
