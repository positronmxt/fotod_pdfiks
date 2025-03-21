# Fotod PDFiks

Tööriist telefonis pildistatud dokumentide konverteerimiseks kompaktseteks PDF-failideks.

## Funktsioonid

- Dokumendi automaatne tuvastamine ja kärpimine fotost
- Perspektiivi korrigeerimine (dokumendi sirgestamine)
- Pildi kvaliteedi parandamine (kontrast, teravus, müra eemaldamine)
- Mitme pildi ühendamine üheks PDF-failiks
- Kompaktsete PDF-failide loomine
- Graafiline kasutajaliides lihtsamaks kasutamiseks
- Veebipõhine kasutajaliides (ei vaja Tkinter moodulit)

## Paigaldamine

### Automaatne paigaldamine (soovitatud)

```bash
# Linux/macOS:
chmod +x install.sh  # Tee skript käivitatavaks (kui pole juba)
./install.sh

# Windows:
# Topeltklikk failil install.bat
```

Automaatne installeerimine:
- Kontrollib ja paigaldab vajalikud sõltuvused
- Seadistab Python virtuaalkeskkonna
- Paigaldab kõik vajalikud Pythoni paketid
- Testib paigaldust, et kindlustada korrektne töö
- Loob lihtsad käivitamise skriptid igapäevaseks kasutamiseks

### Käsitsi paigaldamine

```bash
# Klooni repo
git clone https://github.com/username/fotod_pdfiks.git
cd fotod_pdfiks

# Virtuaalkeskkonna loomine ja aktiveerimine (soovitatud)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate    # Windows

# Paigalda sõltuvused
pip install -r requirements.txt

# Tesseract OCR paigaldamine (vajalik teksti tuvastamiseks)
# Ubuntu/Debian
sudo apt-get install tesseract-ocr
# macOS
brew install tesseract
# Windows: Laadi alla installer lehelt https://github.com/UB-Mannheim/tesseract/wiki

# Tee skriptid käivitatavaks
chmod +x fotod_pdfiks.sh demo.sh fotod_pdfiks_gui.sh fotod_pdfiks_web.sh
```

## Kasutamine

### Veebipõhine kasutajaliides (soovitatud)

Kõige lihtsam viis programmi kasutamiseks on veebipõhine kasutajaliides, mis ei vaja Tkinter moodulit:

```bash
# Käivita veebipõhine kasutajaliides
./fotod_pdfiks_web.sh
```

Veebiliides avatakse brauseris (tavaliselt aadressil http://localhost:8501) ja võimaldab:
- Pilte üles laadida brauseri failisirvija abil
- Määrata väljund-PDF faili nimi
- Valida DPI, OCR režiim ja muud seaded
- Näha edenemise infot töötlemise ajal
- Laadida alla loodud PDF-i kohe pärast töötlemist

Täpsema info ja ekraanipiltide jaoks vaata [VEEBILIIDES.md](VEEBILIIDES.md).

### Graafiline kasutajaliides (Tkinter)

Kui sul on Tkinter toega Python, võid kasutada ka graafilist kasutajaliidest:

```bash
# Käivita graafiline kasutajaliides
./fotod_pdfiks_gui.sh
```

Graafiline kasutajaliides võimaldab:
- Pilte valida failisirvija abil või lohistada need otse programmi
- Määrata väljund-PDF faili asukoht
- Valida DPI, OCR režiim ja muud seaded
- Näha edenemise infot töötlemise ajal
- Avada ja eelvaadata PDF-i peale töötlemist

### Shell skripti kasutamine käsureal

Lihtne viis programmi käsureal kasutamiseks on kasutada kaasasolevaid shell skripte:

```bash
# Demo käivitamine
./demo.sh

# Ühe pildi konverteerimine PDF-iks
./fotod_pdfiks.sh --input pilt.jpg --output dokument.pdf

# Mitme pildi konverteerimine üheks PDF-iks
./fotod_pdfiks.sh --input pildid_kaust/ --output dokument.pdf

# Täiendavad võimalused
./fotod_pdfiks.sh --help
```

### Otse Pythoni skriptiga

Kui soovid käivitada otse Python skripti virtuaalkeskkonnas:

```bash
# Aktiveeri virtuaalkeskkond
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate    # Windows

# Ühe pildi konverteerimine PDF-iks
python fotod_pdfiks.py --input pilt.jpg --output dokument.pdf

# Mitme pildi konverteerimine üheks PDF-iks
python fotod_pdfiks.py --input pildid_kaust/ --output dokument.pdf

# Täiendavad võimalused
python fotod_pdfiks.py --help

# Deaktiveeri virtuaalkeskkond, kui oled lõpetanud
deactivate
```

## Nõuded

- Python 3.8+
- OpenCV
- Pillow
- img2pdf
- pytesseract
- Tesseract OCR
- Streamlit (veebiliidese jaoks)
- tkinter (Tkinter-põhise graafilise kasutajaliidese jaoks, valikuline)

## Litsents

MIT 