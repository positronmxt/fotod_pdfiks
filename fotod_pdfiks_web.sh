#!/bin/bash

# See skript käivitab Fotod PDFiks veebirakenduse

# Tühista keskkonna muutujad, mis võivad tekitada probleeme
unset PYTHONHOME
unset PYTHONPATH

# Määra skripti kataloog
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Aktiveeri virtuaalkeskkond ja käivita Streamlit rakendus
source venv/bin/activate
streamlit run fotod_pdfiks_web.py "$@"
deactivate

exit 0 