#!/bin/bash

# Fotod PDFiks GUI käivitamise skript
# See skript tühistab probleemsed keskkonna muutujad ja käivitab fotod_pdfiks_gui.py programmi

# Tühistame probleemsed keskkonna muutujad
unset PYTHONHOME PYTHONPATH

# Skripti asukoha tuvastamine
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Käivita GUI programm
cd "$SCRIPT_DIR"
source venv/bin/activate
python fotod_pdfiks_gui.py
deactivate

# Lõpeta õnnestumisega
exit 0 