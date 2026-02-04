# Instruções de Deploy - Funcionalidade de Exclusão de Leads

Esta atualização implementa a funcionalidade de **Soft Delete** para leads no módulo de Marketing & CRM.

## Alterações Realizadas

### Backend
- **Modelos**: Adicionados campos `is_deleted` e `deleted_at` ao modelo `Lead`.
- **Endpoints**:
  - `GET /api/marketing/leads`: Agora filtra leads deletados por padrão (suporta `?include_deleted=true`).
  - `DELETE /api/marketing/leads/<id>`: Implementado como Soft Delete.
  - `POST /api/marketing/leads/<id>/restore`: Novo endpoint para restaurar leads.
- **Auto-reparo**: A função `/api/fix_tables` foi atualizada para incluir as novas colunas automaticamente.

### Frontend
- **Kanban**: Adicionado ícone de lixeira em cada card de lead.
- **UX**: Implementado modal de confirmação nativo e feedback visual de carregamento durante a exclusão.
- **Estado**: Remoção imediata do lead do board após exclusão bem-sucedida.

## Como aplicar a migração no Render

Existem duas formas de aplicar as alterações no banco de dados:

### Opção 1: Via API de Reparo (Recomendado)
Após o deploy do novo código, acesse a seguinte URL no seu navegador (substitua pelo seu domínio):
`https://seu-app-no-render.com/api/fix_tables`

Isso executará os comandos `ALTER TABLE` necessários para adicionar as colunas sem perder dados existentes.

### Opção 2: Via Console SQL do Render
1. Acesse o Dashboard do Render.
2. Vá em **Databases** e selecione o banco do projeto.
3. Clique em **Console**.
4. Copie e cole o conteúdo do arquivo `migration_soft_delete.sql` e execute.

## Arquivos Alterados
- `backend/app/models.py`
- `backend/app/__init__.py`
- `backend/app/routes/marketing/campaigns.py`
- `src/pages/MarketingCRM.tsx`
