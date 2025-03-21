#!/bin/bash

set -e  # Lõpeta, kui ilmneb viga

# Värvid konsooliteadete jaoks
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logo ja tervitustekst
echo -e "${BLUE}"
echo "========================================"
echo "   Fotod PDFiks - Installatsiooniskript"
echo "========================================"
echo -e "${NC}"

# Funktsioon kasutaja teavitamiseks
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Funktsioon hoiatussõnumite jaoks
warning() {
    echo -e "${YELLOW}[HOIATUS]${NC} $1"
}

# Funktsioon edukate toimingute jaoks
success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# Funktsioon vigade jaoks
error() {
    echo -e "${RED}[VIGA]${NC} $1"
    exit 1
}

# Kontrolli, kas Python on paigaldatud
check_python() {
    info "Kontrollin Pythoni olemasolu..."
    if command -v python3 &>/dev/null; then
        python_version=$(python3 --version | cut -d " " -f 2)
        success "Python $python_version leitud."
    else
        error "Python pole paigaldatud. Palun paigalda Python 3.8 või uuem versioon."
    fi
}

# Kontrolli, kas pip on paigaldatud
check_pip() {
    info "Kontrollin pip-i olemasolu..."
    if python3 -m pip --version &>/dev/null; then
        pip_version=$(python3 -m pip --version | awk '{print $2}')
        success "pip $pip_version leitud."
    else
        warning "pip pole paigaldatud või pole leitav. Proovime selle paigaldada..."
        install_pip
    fi
}

# Paigalda pip, kui see puudub
install_pip() {
    info "Paigaldan pip..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update
        sudo apt-get install -y python3-pip
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3-pip
    elif command -v zypper &>/dev/null; then
        sudo zypper install -y python3-pip
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm python-pip
    else
        error "Ei suutnud pip-i automaatselt paigaldada. Palun paigalda see käsitsi."
    fi
    
    if python3 -m pip --version &>/dev/null; then
        success "pip paigaldatud."
    else
        error "pip-i paigaldamine ebaõnnestus."
    fi
}

# Kontrolli, kas Tesseract on paigaldatud
check_tesseract() {
    info "Kontrollin Tesseract OCR olemasolu..."
    if command -v tesseract &>/dev/null; then
        tesseract_version=$(tesseract --version | head -n 1 | awk '{print $2}')
        success "Tesseract OCR $tesseract_version leitud."
    else
        warning "Tesseract OCR pole paigaldatud. Proovime selle paigaldada..."
        install_tesseract
    fi
}

# Kontrolli, kas Poppler-utils on paigaldatud (vajalik pdf2image jaoks)
check_poppler() {
    info "Kontrollin Poppler-utils olemasolu (vajalik PDF töötlemiseks)..."
    if command -v pdftoppm &>/dev/null; then
        poppler_version=$(pdftoppm -v 2>&1 | head -n 1 | awk '{print $3}')
        success "Poppler-utils $poppler_version leitud."
    else
        warning "Poppler-utils pole paigaldatud. Proovime selle paigaldada..."
        install_poppler
    fi
}

# Paigalda Tesseract, kui see puudub
install_tesseract() {
    info "Paigaldan Tesseract OCR..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr
        # Eesti keele pakett
        sudo apt-get install -y tesseract-ocr-est
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y tesseract
        # Eesti keele pakett
        sudo dnf install -y tesseract-langpack-est
    elif command -v zypper &>/dev/null; then
        sudo zypper install -y tesseract-ocr
        # Eesti keele pakett
        sudo zypper install -y tesseract-ocr-traineddata-est
    elif command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm tesseract
        sudo pacman -S --noconfirm tesseract-data-est
    elif command -v brew &>/dev/null; then
        brew install tesseract
        # Eesti keele pakett
        brew install tesseract-lang
    else
        error "Ei suutnud Tesseract OCR-i automaatselt paigaldada. Palun paigalda see käsitsi: https://github.com/tesseract-ocr/tesseract"
    fi
    
    if command -v tesseract &>/dev/null; then
        success "Tesseract OCR paigaldatud."
    else
        error "Tesseract OCR paigaldamine ebaõnnestus."
    fi
}

# Paigalda Poppler-utils, kui see puudub
install_poppler() {
    info "Paigaldan Poppler-utils..."
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
}

# Kontrolli, kas tkinter on paigaldatud (vabatahtlik sõltuvus)
check_tkinter() {
    info "Kontrollin tkinter'i olemasolu (vabatahtlik)..."
    if python3 -c "import tkinter" &>/dev/null; then
        success "tkinter leitud."
    else
        warning "tkinter pole paigaldatud. GUI kasutajaliides ei ole saadaval, aga veebiliides töötab."
        warning "Kui soovid kasutada GUI kasutajaliidest, paigalda tkinter."
        if command -v apt-get &>/dev/null; then
            echo "  sudo apt-get install -y python3-tk"
        elif command -v dnf &>/dev/null; then
            echo "  sudo dnf install -y python3-tkinter"
        elif command -v zypper &>/dev/null; then
            echo "  sudo zypper install -y python3-tk"
        elif command -v pacman &>/dev/null; then
            echo "  sudo pacman -S --noconfirm python-tk"
        elif command -v brew &>/dev/null; then
            echo "  brew install python-tk"
        fi
    fi
}

# Kontrolli ja loo virtuaalkeskkond
setup_virtualenv() {
    info "Kontrollin virtuaalkeskkonna olemasolu..."
    if [ -d "venv" ]; then
        success "Virtuaalkeskkond 'venv' juba olemas."
    else
        info "Loon uue virtuaalkeskkonna..."
        python3 -m venv venv
        success "Virtuaalkeskkond 'venv' loodud."
    fi
    
    info "Aktiveerin virtuaalkeskkonna..."
    source venv/bin/activate
    success "Virtuaalkeskkond aktiveeritud."
}

# Paigalda vajalikud Pythoni sõltuvused
install_python_deps() {
    info "Paigaldan Pythoni sõltuvusi..."
    python3 -m pip install --upgrade pip
    
    # Paigalda setuptools eraldi ja veendu, et see on korralikult installitud
    info "Paigaldan setuptools (vajalik teiste pakettide ehitamiseks)..."
    python3 -m pip install --upgrade setuptools wheel
    
    # Kontrolli Python versiooni
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    info "Python versioon: $python_version"
    
    # Python 3.12 ja uuemate versioonide puhul on vaja erisusi
    if [[ "$python_version" == "3.12" || "$python_version" > "3.12" ]]; then
        info "Kasutan Python 3.12+ spetsiifilist paigaldusmeetodit..."
        
        # Proovi paigaldada numpy esmalt binaarfailidena
        info "Paigaldan numpy binaarfailina..."
        python3 -m pip install --only-binary=:all: numpy --no-build-isolation
        
        # Paigalda OpenCV
        info "Paigaldan OpenCV..."
        python3 -m pip install opencv-python --no-build-isolation
        
        # Paigalda ülejäänud paketid nimekirjast
        info "Paigaldan ülejäänud paketid..."
        while IFS= read -r package || [[ -n "$package" ]]; do
            # Jäta vahele kommentaarid ja tühjad read
            if [[ $package != \#* && -n "$package" ]]; then
                # Jäta vahele juba paigaldatud paketid (numpy ja opencv)
                if [[ "$package" != "numpy"* && "$package" != "opencv"* ]]; then
                    info "Paigaldan: $package"
                    python3 -m pip install --only-binary=:all: "$package" || {
                        warning "Ei saanud paigaldada $package ainult binaaridega, proovin uuesti..."
                        python3 -m pip install "$package" --no-build-isolation || 
                            warning "Paketi $package paigaldamine ebaõnnestus."
                    }
                fi
            fi
        done < requirements.txt
        
        # Kontrolli, kas streamlit on puudu
        if ! python3 -c "import streamlit" &>/dev/null; then
            info "Paigaldan Streamlit (veebiliidese jaoks)..."
            python3 -m pip install streamlit --no-build-isolation
        fi
        
    # Varasemad Python versioonid kasutavad tavalisemat paigaldusmeetodit
    else
        # Kontrolli, kas setuptools paigaldati edukalt
        if ! python3 -c "import setuptools.build_meta" &>/dev/null; then
            warning "setuptools.build_meta importimine ebaõnnestus. Proovin paketid paigaldada alternatiivse meetodiga."
            # Paigalda igaüks eraldi
            for package in $(cat requirements.txt | grep -v "#"); do
                info "Paigaldan paketi: $package"
                python3 -m pip install --no-build-isolation "$package" || warning "Paketi $package paigaldamine ebaõnnestus. Jätkan järgmisega."
            done
        else
            # Kui setuptools on korralikult paigaldatud, jätka tavapäraselt
            info "Paigaldan pakette requirements.txt failist..."
            python3 -m pip install -r requirements.txt
        fi
        
        # Kontrolli, kas streamlit on puudu requirements.txt-st
        if ! grep -q "streamlit" requirements.txt; then
            info "Paigaldan Streamlit (veebiliidese jaoks)..."
            python3 -m pip install streamlit
        fi
    fi
    
    success "Kõik Pythoni sõltuvused paigaldatud."
}

# Tee skriptid käivitatavaks
make_scripts_executable() {
    info "Teen skriptid käivitatavaks..."
    chmod +x fotod_pdfiks.py fotod_pdfiks_gui.py fotod_pdfiks_web.py
    chmod +x fotod_pdfiks.sh fotod_pdfiks_gui.sh fotod_pdfiks_web.sh demo.sh
    success "Skriptid on nüüd käivitatavad."
}

# Kontrolli, kas Git on paigaldatud
check_git() {
    info "Kontrollin Git'i olemasolu..."
    if command -v git &>/dev/null; then
        git_version=$(git --version | awk '{print $3}')
        success "Git $git_version leitud."
    else
        warning "Git pole paigaldatud. Kui soovid programmi arendada või uuendada, võiksid Git-i paigaldada."
        if command -v apt-get &>/dev/null; then
            echo "  sudo apt-get install -y git"
        elif command -v dnf &>/dev/null; then
            echo "  sudo dnf install -y git"
        elif command -v zypper &>/dev/null; then
            echo "  sudo zypper install -y git"
        elif command -v pacman &>/dev/null; then
            echo "  sudo pacman -S --noconfirm git"
        elif command -v brew &>/dev/null; then
            echo "  brew install git"
        fi
    fi
}

# Loo lühike lemmikute skript kasutajale
create_shortcut_script() {
    info "Loon lühilingi lihtsamaks kasutamiseks..."
    cat > fotod_pdfiks_kasuta.sh << 'EOL'
#!/bin/bash
# Lihtne lühinlink Fotod PDFiks käivitamiseks

# Leia skripti asukoht
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
cd "$SCRIPT_DIR"

# Käivita veebiliides
source venv/bin/activate
echo "Käivitan Fotod PDFiks veebiliidese..."
echo "Palun oota, brauseris avaneb veebiliides..."
streamlit run fotod_pdfiks_web.py
EOL

    chmod +x fotod_pdfiks_kasuta.sh
    success "Lühilink 'fotod_pdfiks_kasuta.sh' loodud."
}

# Programmi testikäivitus
test_run() {
    info "Testin programmi..."
    if [ -f "test_input.jpg" ]; then
        info "Testin demo skripti..."
        ./demo.sh
        success "Demo test läbitud!"
    else
        warning "Testpilt 'test_input.jpg' puudub, ei saa testi käivitada."
    fi
}

# Peamine funktsioon kõigi sammude käivitamiseks
main() {
    check_python
    check_pip
    check_tesseract
    check_poppler
    check_tkinter
    check_git
    setup_virtualenv
    install_python_deps
    make_scripts_executable
    create_shortcut_script
    
    echo -e "${GREEN}"
    echo "========================================"
    echo "   Paigaldamine edukalt lõpetatud!"
    echo "========================================"
    echo -e "${NC}"
    echo "Programmi käivitamiseks:"
    echo "  Veebiliides: ./fotod_pdfiks_web.sh"
    echo "  GUI (kui on tkinter): ./fotod_pdfiks_gui.sh"
    echo "  Lihtsaim viis: ./fotod_pdfiks_kasuta.sh"
    echo ""
    echo "Täpsemad kasutusjuhised: README.md"
    
    # Küsi, kas kasutaja soovib testida programmi
    read -p "Kas soovid kohe programmi testida? (j/e) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Jj]$ ]]; then
        test_run
    fi
}

# Käivita peamine funktsioon
main 