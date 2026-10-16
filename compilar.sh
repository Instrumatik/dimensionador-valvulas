#!/bin/sh
# Compila el dimensionador en macOS o Linux (Python 3.11+). Resultado en dist/.
set -e
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt
QT_QPA_PLATFORM=offscreen python3 -m pytest -q tests
python3 -m PyInstaller --noconfirm dimensionador.spec
echo "Listo: carpeta dist/"
