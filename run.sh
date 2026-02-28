#!/bin/bash
# Script de inicio rápido para el servicio

set -e

# Verificar si existe .env
if [ ! -f .env ]; then
    echo "⚠️  No se encontró archivo .env"
    echo "📝 Copiando .env.example a .env..."
    cp .env.example .env
    echo "✅ Archivo .env creado. Por favor configura tus credenciales de BioTime."
    exit 1
fi

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️  No se encontró entorno virtual."
    echo "💡 Crea uno con: python -m venv venv"
    exit 1
fi

# Verificar dependencias
pip install -q -r requirements.txt

# Ejecutar la aplicación
python -m app.main
