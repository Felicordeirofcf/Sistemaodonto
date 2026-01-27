#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Iniciando processo de Build..."

# 1. Instalar dependências do Backend (Python)
echo "🐍 Instalando dependências do Python..."
pip install -r backend/requirements.txt

# 2. Instalar dependências do Frontend (Node) e Buildar
echo "📦 Instalando e buildando o Frontend..."
npm install
npm run build

# 3. Organizar os arquivos estáticos para o Flask
# Criamos a pasta static dentro de backend/app se não existir
echo "🚚 Movendo arquivos para o diretório static..."
mkdir -p backend/app/static

# Limpamos o conteúdo antigo da pasta static, mas SEM deletar a pasta em si
# Isso evita erros de permissão e garante que o auto_migrate.py continue lá
rm -rf backend/app/static/*

# Copia o build do React para a pasta static do Flask
cp -r dist/* backend/app/static/

echo "✅ Build finalizado com sucesso!"