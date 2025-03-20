# Fotod PDFiks - Kasutamisjuhend

See programm võimaldab telefonis pildistatud dokumendid optimeerida ja konverteerida kompaktseks PDF-failiks.

## Paigaldamine

```bash
# Klooni repo
git clone https://github.com/yourusername/fotod_pdfiks.git
cd fotod_pdfiks

# Paigalda sõltuvused
pip install -r requirements.txt

# Tesseract OCR paigaldamine (vajalik OCR funktsioonideks)
# Ubuntu/Debian
sudo apt-get install tesseract-ocr
# macOS
brew install tesseract
# Windows: Laadi alla installer lehelt https://github.com/UB-Mannheim/tesseract/wiki
```

## Kasutamine

### Põhikasutus

Ühe dokumendifoto konverteerimine PDF-iks:

```bash
python fotod_pdfiks.py --input dokument.jpg --output tulemus.pdf
```

### Kausta töötlemine

Kõigi kataloogis olevate piltide konverteerimine üheks PDF-iks:

```bash
python fotod_pdfiks.py --input pildid/ --output dokumendid.pdf
```

### DPI muutmine

DPI (punktid tolli kohta) määramine väljund-PDF jaoks:

```bash
python fotod_pdfiks.py --input dokument.jpg --output tulemus.pdf --dpi 300
```

### Debug režiim

Debug režiim salvestab töötlemise vaheetapid eraldi kausta:

```bash
python fotod_pdfiks.py --input dokument.jpg --output tulemus.pdf --debug
```

### OCR teksti tuvastamine

Teksti tuvastamine piltidelt (eeldab Tesseract OCR olemasolu):

```bash
python fotod_pdfiks.py --input dokument.jpg --output tulemus.pdf --ocr
```

OCR keele määramine (vaikimisi inglise keel - eng):

```bash
python fotod_pdfiks.py --input dokument.jpg --output tulemus.pdf --ocr --lang est
```

## Näpunäited

1. **Parimate tulemuste saamiseks**:
   - Pildista dokument ühtlasel taustal ja hea valgustusega
   - Väldi varje ja peegeldusi
   - Veendu, et kogu dokument on pildil nähtav

2. **Vähendatud failimahu jaoks**:
   - Kasuta madalat DPI väärtust (nt 150) kui tekst on selge
   - Kõrgemat DPI-d (300+) kasuta kui tekst on väike või vajad kvaliteetsemat tulemust

3. **Mitmeleheliste dokumentide puhul**:
   - Pildista lehed eraldi ja pane piltidele sellised nimed, mis tagavad korrektse järjestuse (nt 01_lehekülg.jpg, 02_lehekülg.jpg)
   - Kasuta kausta töötlemise režiimi

4. **Kui automaatne dokumendi tuvastamine ei tööta**:
   - Veendu, et dokument on selgelt nähtav taustast erineva kontrastiga
   - Pildi parandatud versioonid leiab debug režiimis loodud kaustast 