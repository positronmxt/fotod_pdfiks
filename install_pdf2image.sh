#!/bin/bash

# Värvid konsooliteadete jaoks
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funktsioonid teadete jaoks
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
warning() { echo -e "${YELLOW}[HOIATUS]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
error() { echo -e "${RED}[VIGA]${NC} $1"; exit 1; }

echo "==== pdf2image paketi paigaldus ===="
echo

# Kontrolli, kas virtuaalkeskkond on olemas
if [ ! -d "venv" ]; then
    error "Virtuaalkeskkond puudub. Palun käivita esmalt ./install.sh"
fi

# Aktiveeri virtuaalkeskkond
info "Aktiveerin virtuaalkeskkonna..."
source venv/bin/activate
success "Virtuaalkeskkond aktiveeritud."

# Kontrolli, kas Poppler-utils on paigaldatud
info "Kontrollin Poppler-utils olemasolu (vajalik PDF töötlemiseks)..."
if command -v pdftoppm &>/dev/null; then
    poppler_version=$(pdftoppm -v 2>&1 | head -n 1 | awk '{print $3}')
    success "Poppler-utils $poppler_version leitud."
else
    warning "Poppler-utils pole paigaldatud. Proovime selle paigaldada..."
    
    # Paigalda Poppler-utils
    if command -v apt-get &>/dev/null; then
        sudo apt-get update
        sudo apt-get install -y poppler-utils
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y poppler-utils
    elif command -v zypper &>/dev/null; then
        sudo zypper install -y poppler-tools
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm poppler
    elif command -v brew &>/dev/null; then
        brew install poppler
    else
        warning "Ei suutnud Poppler-utils automaatselt paigaldada. PDF-failide töötlemine võib olla piiratud."
        warning "Palun paigalda Poppler-utils käsitsi oma süsteemi jaoks."
    fi
    
    if command -v pdftoppm &>/dev/null; then
        success "Poppler-utils paigaldatud."
    else
        warning "Poppler-utils paigaldamine ebaõnnestus. PDF-failide töötlemine võib olla piiratud."
    fi
fi

# Paigalda pdf2image
info "Paigaldan pdf2image paketi..."
python -m pip install pdf2image>=1.16.0

# Kontrolli, kas paigaldus õnnestus
if python -c "import pdf2image" &>/dev/null; then
    success "pdf2image on nüüd paigaldatud!"
    echo 
    echo "Käivita programm uuesti käsuga:"
    echo "./fotod_pdfiks_kasuta.sh"
    echo
else
    error "pdf2image paigaldamine ebaõnnestus."
fi 