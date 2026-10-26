#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$(realpath "$0")")"

if [[ ! -x .venv/bin/python ]]; then
    echo "Preparando el entorno virtual..."
    python3 -m venv .venv
fi

if [[ ! -f .venv/.requirements-installed ]] || ! cmp -s requirements.txt .venv/.requirements-installed; then
    if ! .venv/bin/python -m pip install -r requirements.txt; then
        echo "No se pudieron instalar las dependencias de Python." >&2
        echo "Comprueba la conexión e inténtalo de nuevo con: .venv/bin/python -m pip install -r requirements.txt" >&2
        exit 1
    fi
    cp requirements.txt .venv/.requirements-installed
fi

show_help=false
for arg in "$@"; do
    [[ "$arg" == "-h" || "$arg" == "--help" ]] && show_help=true
done

if [[ "$show_help" == false && ( " ${*:-} " == *" --gui "* || " ${*:-} " == *" -g "* ) ]]; then
    if ! .venv/bin/python -c 'import tkinter' >/dev/null 2>&1; then
        echo "El modo GUI necesita Tkinter, que no se instala desde pip." >&2
        echo "Fedora: sudo dnf install python3-tkinter" >&2
        echo "Debian/Ubuntu: sudo apt install python3-tk" >&2
        echo "Arch Linux: sudo pacman -S tk" >&2
        exit 1
    fi
fi

exec .venv/bin/python src/main.py "$@"
