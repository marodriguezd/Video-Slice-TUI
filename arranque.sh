#!/bin/bash

# Navegar al directorio del script
cd "$(dirname "$0")"

# Verificar si el entorno virtual existe
if [ ! -d ".venv" ]; then
    echo "Error: No se encontró el directorio .venv."
    echo "Por favor, créalo con: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Ejecutar la aplicación pasando todos los argumentos con exec para reemplazar el proceso
exec ./.venv/bin/python3 src/main.py "$@"
