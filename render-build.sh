#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🚀 Iniciando processo de Build Industrial..."

# 1. Instalar dependências do Backend (Python)
echo "🐍 Instalando dependências do Python..."
pip install --upgrade pip
pip install -r backend/requirements.txt

# 2. Instalar dependências do Frontend (Node) e Buildar
echo "📦 Instalando e buildando o Frontend (Vite/React)..."
npm install
npm run build

# 3. Organizar os arquivos estáticos para o Flask
echo "🚚 Limpando e movendo build para o diretório static..."
mkdir -p backend/app/static

# Limpeza seletiva para evitar problemas de concorrência no Render
find backend/app/static -mindepth 1 -delete

# Copia o build final
cp -r dist/* backend/app/static/

echo "✅ Build finalizado com sucesso! Pronto para o deploy."