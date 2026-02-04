> # OdontoSys - Revisão, SaaS e Chatbot
> 
> Este documento detalha as correções aplicadas no sistema OdontoSys, focando no modelo SaaS, Chatbot automático e Agenda funcional.

## Novidades desta Versão

### 🤖 Chatbot Inteligente (WhatsApp)
- **Resposta Automática**: O sistema agora detecta leads vindos de campanhas específicas (via código `[ref:CODE]`) e envia uma saudação automática personalizada.
- **Fluxo de Atendimento**: Mensagens recebidas são registradas no histórico do CRM em tempo real, permitindo que o dentista veja toda a conversa antes de assumir o atendimento manual.
- **Filtro de Grupos**: O bot ignora automaticamente grupos e mensagens enviadas pelo próprio número da clínica, focando apenas em novos pacientes.

### 🏢 Arquitetura SaaS (Multi-Clínica)
- **Isolamento Total**: Cada novo registro no sistema cria uma `Clinic` (Tenant) isolada.
- **Instâncias Independentes**: O sistema gera nomes de instâncias únicos para o WhatsApp (`clinica_v3_{id}`), permitindo que centenas de clínicas usem o mesmo servidor Evolution API com números diferentes.
- **Segurança de Dados**: Todas as rotas de API (Agenda, Pacientes, Financeiro, Marketing) utilizam o `clinic_id` extraído do token JWT para garantir que um usuário nunca acesse dados de outra clínica.

### 📅 Agenda 100% Funcional
- **Gestão de Horários**: Interface drag-and-drop (simulada) com suporte a status (Agendado, Confirmado, Concluído, Cancelado).
- **Conversão de Leads**: Botão "Agendar" dentro do CRM que transporta os dados do lead diretamente para a agenda, economizando tempo de digitação.

---

## Instruções de Deploy (Render)

### 1. Variáveis de Ambiente (Backend)
| Variável | Descrição | Exemplo |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL URL | `postgresql://user:pass@host/dbname` |
| `JWT_SECRET_KEY` | Chave de segurança | `sua-chave-secreta` |
| `WHATSAPP_QR_SERVICE_URL` | URL da Evolution API | `https://sua-evolution-api.com` |
| `EVOLUTION_API_KEY` | API Key da Evolution | `429683C4C977415CAAF6...` |
| `OPENAI_API_KEY` | Chave OpenAI (atendimento ChatGPT) | `sk-...` |
| `OPENAI_MODEL` | Modelo (opcional) | `gpt-4o-mini` |

### 2. Comandos de Build
- **Build Command**: `./render-build.sh`
- **Start Command**: `cd backend && python auto_migrate.py && gunicorn run:app`
- **Frontend**: `npm install && npm run build` (Diretório de saída: `dist`)

### 3. Webhook (Configuração na Evolution API)
Para o Chatbot funcionar, você deve configurar o Webhook na sua Evolution API apontando para:
`https://seu-backend.render.com/api/marketing/webhook/whatsapp`
- **Eventos**: `MESSAGES_UPSERT`

---

## Credenciais de Teste (Local)
Se rodar o `seed_db.py`, use:
- **Login**: `admin@odonto.com`
- **Senha**: `admin123`

---
*Desenvolvido por Manus AI para Sistema OdontoSys.*
