-- Script de Migração: Adicionar Soft Delete para Leads
-- Este script deve ser executado no banco de dados (PostgreSQL no Render)

-- 1. Adicionar colunas de soft delete na tabela marketing_leads
ALTER TABLE marketing_leads ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE marketing_leads ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITHOUT TIME ZONE NULL;

-- 2. Criar índice para otimizar a filtragem de leads ativos por clínica
CREATE INDEX IF NOT EXISTS idx_leads_clinic_deleted ON marketing_leads (clinic_id, is_deleted);

-- 3. (Opcional) Se desejar limpar leads que ficaram órfãos de campanhas excluídas anteriormente
-- UPDATE marketing_leads SET is_deleted = TRUE, deleted_at = NOW() WHERE campaign_id IS NULL AND status = 'perdido';

-- Mensagem de confirmação
DO $$ 
BEGIN 
    RAISE NOTICE 'Migração de Soft Delete concluída com sucesso.';
END $$;
