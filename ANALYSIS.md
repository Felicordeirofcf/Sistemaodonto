# Análise do Sistema OdontoSys

## Problemas Identificados

### Backend
1.  **WhatsApp / Evolution API**:
    *   Necessário garantir que `Clinic.whatsapp_number` seja salvo automaticamente ao conectar via QR Code.
    *   Tratar erro 403 "instance name already in use" como sucesso.
    *   Melhorar o parsing de `owner` / `ownerJid` no `fetchInstances`.
2.  **Webhook WhatsApp**:
    *   Ignorar mensagens de grupos (`@g.us`).
    *   Ignorar mensagens `fromMe`.
    *   Extrair texto de múltiplos formatos (`conversation`, `extendedTextMessage`, `buttonsResponseMessage`, `listResponseMessage`).
    *   Identificar `tracking_code` (`[ref:CODE]`) e criar/atualizar `Lead` + `CRMCard`.
    *   Evitar duplicidade de cards para o mesmo telefone.
3.  **Agenda**:
    *   O modelo `Appointment` atual é básico. Precisa de `start_datetime`, `end_datetime`, `patient_id`, `lead_id`, `status` (scheduled|confirmed|done|cancelled).
    *   Endpoints de CRUD completos estão incompletos ou ausentes.
4.  **CRM**:
    *   Endpoint `/crm/board` precisa retornar `paciente_nome`, `paciente_phone`, `ultima_interacao` e `origem/campanha`.

### Frontend
1.  **Menu/Sidebar**:
    *   Remover "Odontograma" e "AtendeChat IA".
2.  **Agenda**:
    *   A UI atual usa dados estáticos (fallback) e não tem um CRUD funcional integrado ao backend.
    *   Falta integração com o CRM (botão "Agendar" no card do lead).
3.  **CRM**:
    *   Exibir origem/campanha nos cards do Kanban.

## Plano de Ação

### 1. Backend (Correções e Melhorias)
*   Atualizar `models.py` com novos campos na `Appointment`.
*   Ajustar `whatsapp.py` para auto-save do número e tratamento de erros da Evolution API.
*   Refatorar `webhook.py` para processamento robusto de mensagens e leads.
*   Implementar CRUD completo em `agenda_routes.py`.

### 2. Frontend (UI e Integração)
*   Modificar `Sidebar.tsx` para remover itens solicitados.
*   Refatorar `Agenda.tsx` para usar os novos endpoints e permitir agendamento real.
*   Adicionar funcionalidade de agendamento a partir do CRM em `MarketingPage.tsx`.

### 3. Deploy e Finalização
*   Garantir variáveis de ambiente.
*   Preparar script de migração/criação de tabelas.
*   Gerar ZIP final.
