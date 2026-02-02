#!/usr/bin/env bash
set -o errexit

echo "🚀 Iniciando processo de Build Industrial..."

# =========================================
# 1) Backend (Python)
# =========================================
echo "🐍 Instalando dependências do Python..."
python -m pip install --upgrade pip
pip install -r backend/requirements.txt

# =========================================
# 2) Frontend (Vite/React)
# =========================================
echo "📦 Instalando dependências do Frontend (Vite/React)..."

if [ -f package-lock.json ]; then
  echo "🔒 package-lock.json encontrado → usando npm ci (build mais estável)"
  npm ci
else
  echo "ℹ️ package-lock.json não encontrado → usando npm install"
  npm install
fi

echo "🏗️ Buildando o Frontend..."
npm run build

# =========================================
# 3) Publicar estáticos para o Flask
# =========================================
echo "🚚 Limpando e movendo build para o diretório static..."

# onde o Flask vai servir os arquivos
mkdir -p backend/app/static

# limpa com segurança
find backend/app/static -mindepth 1 -delete

# valida se dist existe
if [ ! -d "dist" ]; then
  echo "❌ Pasta dist não encontrada. Build do frontend falhou."
  exit 1
fi

# copia tudo do dist (inclui index.html e assets)
cp -R dist/. backend/app/static/

echo "✅ Build finalizado com sucesso! Pronto para o deploy."
