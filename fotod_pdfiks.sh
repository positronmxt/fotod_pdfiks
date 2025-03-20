#!/bin/bash

# Fotod PDFiks käivitamise skript
# See skript tühistab probleemsed keskkonna muutujad ja käivitab fotod_pdfiks.py programmi

# Tühistame probleemsed keskkonna muutujad
unset PYTHONHOME PYTHONPATH

# Skripti asukoha tuvastamine
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Abiteksti kuvamine, kui argumente pole
function show_help {
    echo "Fotod PDFiks - Dokumendifotode konverteerimine PDF-iks"
    echo ""
    echo "Kasutamine:"
    echo "  $0 [valikud]"
    echo ""
    echo "Valikud:"
    echo "  --input <fail_või_kaust>   Sisendfail või -kaust piltidega (kohustuslik)"
    echo "  --output <pdf_fail>        Väljund PDF-fail (kohustuslik)"
    echo "  --dpi <number>             Väljund-PDF resolutsioon (vaikimisi 300)"
    echo "  --debug                    Luba debug režiim"
    echo "  --ocr                      Tuvasta tekst (OCR)"
    echo "  --lang <kood>              OCR keele kood (vaikimisi: eng)"
    echo "  --help                     Kuva see abitekst"
    echo ""
    echo "Näited:"
    echo "  $0 --input dokument.jpg --output tulemus.pdf"
    echo "  $0 --input pildid/ --output dokumendid.pdf --dpi 300 --ocr --lang est"
    echo ""
}

# Kui argumente pole, kuva abitekst
if [ $# -eq 0 ]; then
    show_help
    exit 1
fi

# Kui esimene argument on --help, kuva abitekst
if [ "$1" == "--help" ]; then
    show_help
    exit 0
fi

# Käivita Python skript koos argumentidega
cd "$SCRIPT_DIR"
source venv/bin/activate
python fotod_pdfiks.py "$@"
deactivate

# Lõpeta õnnestumisega
exit 0 