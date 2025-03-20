#!/bin/bash

# Fotod PDFiks Demo käivitamise skript
# See skript tühistab probleemsed keskkonna muutujad ja käivitab demo.py programmi

# Tühistame probleemsed keskkonna muutujad
unset PYTHONHOME PYTHONPATH

# Skripti asukoha tuvastamine
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Käivita demo skript
cd "$SCRIPT_DIR"
python3 demo.py

# Lõpeta õnnestumisega
exit 0 