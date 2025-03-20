# Fotod PDFiks Veebiliides

See programm pakub veebipõhist kasutajaliidest fotode PDFiks konverteerimiseks, mis ei vaja Tkinter moodulit.

## Käivitamine

Veebiliidese käivitamiseks kasuta käsku:

```bash
./fotod_pdfiks_web.sh
```

Pärast käivitamist näed terminalis midagi sellist:

```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

Ava brauseris näidatud URL (tavaliselt http://localhost:8501).

## Kasutamine

Veebiliides on intuitiivne ja lihtne kasutada:

1. **Failide valimine**: Klõpsa "Vali pildifailid" ala või lohista failid sinna. Saad valida mitu faili korraga.

2. **Väljundfaili määramine**: Sisesta soovitud PDF faili nimi väljundiks (vaikimisi "dokument.pdf").

3. **Parameetrite seadistamine**:
   - **DPI**: Vali lahutusvõime (150, 200, 300, 400 või 600).
   - **OCR**: Märgi linnuke, kui soovid teksti tuvastada.
   - **OCR keel**: Kui OCR on lubatud, vali teksti tuvastamise keel.
   - **Debug režiim**: Märgi linnuke, kui soovid salvestada vaheetappe.

4. **Konverteerimine**: Klõpsa "Konverteeri PDF-iks" nuppu alustamiseks.

5. **Tulemuse allalaadimine**: Pärast edukat konverteerimist saad loodud PDF faili alla laadida.

## Veebiliidese eelised

- **Ei vaja Tkinter moodulit**: Toimib igasuguses Python keskkonnas, kus on paigaldatud Streamlit.
- **Intuitiivne kasutamine**: Kaasaegne ja lihtne kasutajaliides.
- **Eelvaade**: Näed valitud piltide eelvaadet.
- **Reaalajas protsessi jälgimine**: Näed progressiriba ja detailset logi kogu protsessi ajal.
- **Lihtne allalaadimine**: Konverteeritud PDF-i saab kohe alla laadida ilma vajaduseta otsida loodud faili.

## Nõuded

- Python 3.6 või uuem
- Virtuaalkeskkond seadistatud vajalike pakettidega (Streamlit, PIL, jne)
- Samad nõuded, mis põhiprogrammil (Tesseract OCR, jne)

## Veaotsing

- Kui veebiliides ei käivitu, kontrolli, et virtuaalkeskkond oleks korrektselt seadistatud.
- Kontrolli, et Streamlit oleks paigaldatud: `pip install streamlit`
- Konverteerimise probleemide korral vaata logi ala veebiliideses. 