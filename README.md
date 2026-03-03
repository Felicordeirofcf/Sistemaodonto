

🦷 Sistema Odonto SaaS - Gestão Inteligente & IA
Este é um ecossistema completo para gestão de clínicas odontológicas, focado em automação de vendas, controle de lucro líquido real e agendamento inteligente via IA. O sistema foi desenhado sob a arquitetura Multi-tenant, garantindo que os dados de cada clínica sejam isolados e seguros.

🚀 Funcionalidades Principais
🤖 Automação & Marketing (Growth)
Chatbot-IA Integration: Captação de leads via WhatsApp que sincroniza automaticamente com a agenda e o CRM.

CRM Kanban: Funil de vendas para acompanhar pacientes desde o primeiro contato até o fechamento do tratamento.

Campanhas de Recall (Reativação): Algoritmo que identifica pacientes sumidos há mais de 6 meses e sugere mensagens personalizadas baseadas em espaços livres na agenda.

💰 Gestão Financeira & Lucro Real
Fichas Técnicas de Procedimentos: Permite vincular insumos (agulhas, ampolas, luvas) a cada procedimento (ex: Harmonização Facial).

Baixa Automática de Estoque: Ao finalizar uma consulta, o sistema abate os materiais usados e calcula o lucro líquido real (Preço da Consulta - Custo dos Materiais).

Dashboard de Performance: Visualização de faturamento, ROI de campanhas e saúde do estoque em tempo real.

🏥 Operacional Clínico
Agenda Inteligente: Gestão de horários com status de confirmação e pagamento automático.

Prontuário & Odontograma: Registro visual e clínico detalhado da evolução do paciente.

Anamnese Digital: Ficha médica completa com suporte a dados sensíveis em formato JSON.

🛠️ Stack Tecnológica
Backend (SaaS Core)
Python / Flask: API robusta e escalável.

SQLAlchemy / PostgreSQL: Banco de dados relacional com isolamento por clinic_id.

Flask-JWT-Extended: Segurança baseada em tokens com níveis de acesso (Admin vs Dentista).

Frontend (User Experience)
React + TypeScript: Interface rápida, tipada e segura.

Tailwind CSS: Design moderno, responsivo e focado em produtividade.

Lucide React: Iconografia profissional.

Vite: Build otimizado para deploy contínuo no Render/Vercel.

🔒 Segurança & Regras de Negócio (SaaS)
O sistema conta com um motor de regras pronto para monetização:

Role-Based Access (RBAC):

Admin (Dono): Acesso total, financeiro, gestão de equipe e lucro real.

Dentista: Acesso apenas à agenda, prontuários e estoque.

Bloqueio de Inadimplência: Trava global do sistema caso a clínica esteja com o status is_active: false.

Limites de Plano: Restrição automática do número de dentistas cadastrados baseado no plano (Bronze, Prata ou Ouro).

📦 Estrutura do Projeto
Bash
├── backend/
│   ├── app/
│   │   ├── models.py          # Modelagem do banco de dados (PostgreSQL)
│   │   └── routes/            # Lógica de API (Agenda, Marketing, Financeiro...)
│   └── requirements.txt       # Dependências do servidor
├── src/
│   ├── components/            # Sidebar, PrivateRoutes e UI Components
│   ├── pages/                 # Telas (Dashboard, CRM, Estoque, Gestão...)
│   └── App.tsx                # Roteamento e Proteção de Acesso
└── public/                    # Ativos estáticos e PWA
🏁 Como Rodar o Projeto
Backend: Instale as dependências com pip install -r requirements.txt e inicie o Flask.

Frontend: Execute npm install e npm run dev.

Setup de Banco: Para sincronizar novas colunas no Render, acesse a rota: https://seu-dominio.onrender.com/api/setup_db
