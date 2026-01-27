#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Instalar dependências do Python (Backend)
pip install -r backend/requirements.txt

# 2. Instalar dependências do Node (Frontend) e Construir o React
npm install
npm run build

# 3. Mover o build do React para dentro do Backend
# (O Flask vai servir esses arquivos estáticos)
# Limpa pasta antiga se existir
rm -rf backend/app/static
mkdir -p backend/app/static
# Copia o build do React para a pasta static do Flask
cp -r dist/* backend/app/static/