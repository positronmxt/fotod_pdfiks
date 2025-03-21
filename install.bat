@echo off
echo ========================================
echo    Fotod PDFiks - Installatsiooniskript
echo ========================================
echo.

REM Värvid konsooliteadete jaoks
set INFO=[INFO]
set WARNING=[HOIATUS]
set SUCCESS=[OK]
set ERROR=[VIGA]

REM Kontrolli admin õigusi
NET SESSION >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %WARNING% See skript vajab teatud toiminguteks administraatori õigusi.
    echo %WARNING% Mõned osad võivad ebaõnnestuda ilma administraatori õigusteta.
    echo.
    pause
)

REM Kontrolli, kas Python on paigaldatud
echo %INFO% Kontrollin Pythoni olemasolu...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %ERROR% Python pole paigaldatud või pole keskkonnamuutujates.
    echo Palun laadi Python 3.8+ alla ja paigalda: https://www.python.org/downloads/
    echo Märgi kindlasti "Add Python to PATH" paigaldamise ajal.
    pause
    exit /b 1
)

python -c "import sys; print('Python', sys.version.split()[0], 'leitud.')"
echo %SUCCESS% Python leitud.

REM Kontrolli, kas pip on paigaldatud
echo %INFO% Kontrollin pip'i olemasolu...
python -m pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %WARNING% pip pole paigaldatud või pole leitav.
    echo Paigaldan pip'i...
    python -m ensurepip --upgrade
)

python -m pip --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %ERROR% pip'i paigaldamine ebaõnnestus.
    echo Palun paigalda pip käsitsi: https://pip.pypa.io/en/stable/installation/
    pause
    exit /b 1
)
echo %SUCCESS% pip on paigaldatud.

REM Kontrolli või paigalda Tesseract OCR
echo %INFO% Kontrollin Tesseract OCR olemasolu...
where tesseract >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %WARNING% Tesseract OCR pole paigaldatud või pole keskkonnamuutujates.
    echo Palun laadi Tesseract OCR Windows'i jaoks alla ja paigalda:
    echo https://github.com/UB-Mannheim/tesseract/wiki
    echo.
    echo Pärast paigaldamist lisa Tesseract bin kataloog keskkonna Path muutujasse.
    echo Näiteks: C:\Program Files\Tesseract-OCR
    echo.
    echo Kui see on paigaldatud, vajuta suvaline klahv...
    pause
    
    REM Kontrolli uuesti
    where tesseract >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo %ERROR% Tesseract pole endiselt leitav. Palun käivita skript uuesti pärast paigaldamist.
        pause
        exit /b 1
    )
)
echo %SUCCESS% Tesseract OCR leitud.

REM Kontrolli, kas tkinter on paigaldatud (vabatahtlik)
echo %INFO% Kontrollin tkinter'i olemasolu (vabatahtlik)...
python -c "import tkinter" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %WARNING% tkinter pole paigaldatud. GUI kasutajaliides ei ole saadaval.
    echo %WARNING% Veebiliides töötab endiselt.
    echo.
    echo Kui soovid GUI kasutajaliidest, paigalda tkinter:
    echo 1. Ava Python installer uuesti
    echo 2. Vali "Modify"
    echo 3. Märgi "tcl/tk and IDLE"
    echo 4. Kliki "Next" ja "Install"
)
if %ERRORLEVEL% EQU 0 (
    echo %SUCCESS% tkinter leitud.
)

REM Virtuaalkeskkonna kontrollimine ja loomine
echo %INFO% Kontrollin virtuaalkeskkonna olemasolu...
if exist venv (
    echo %SUCCESS% Virtuaalkeskkond 'venv' juba olemas.
) else (
    echo %INFO% Loon uue virtuaalkeskkonna...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo %ERROR% Virtuaalkeskkonna loomine ebaõnnestus.
        pause
        exit /b 1
    )
    echo %SUCCESS% Virtuaalkeskkond 'venv' loodud.
)

REM Aktiveeri virtuaalkeskkond
echo %INFO% Aktiveerin virtuaalkeskkonna...
call venv\Scripts\activate.bat
echo %SUCCESS% Virtuaalkeskkond aktiveeritud.

REM Paigalda vajalikud Pythoni sõltuvused
echo %INFO% Paigaldan Pythoni sõltuvusi...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo %ERROR% Pythoni sõltuvuste paigaldamine ebaõnnestus.
    pause
    exit /b 1
)

REM Kontrolli, kas streamlit on paigaldatud
python -c "import streamlit" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %INFO% Paigaldan Streamlit (veebiliidese jaoks)...
    python -m pip install streamlit
)

echo %SUCCESS% Kõik Pythoni sõltuvused paigaldatud.

REM Loo lühilink kasutamiseks
echo %INFO% Loon lühilingi lihtsamaks kasutamiseks...
echo @echo off > fotod_pdfiks_kasuta.bat
echo echo Käivitan Fotod PDFiks veebiliidese... >> fotod_pdfiks_kasuta.bat
echo echo Palun oota, brauseris avaneb veebiliides... >> fotod_pdfiks_kasuta.bat
echo call venv\Scripts\activate.bat >> fotod_pdfiks_kasuta.bat
echo python -m streamlit run fotod_pdfiks_web.py >> fotod_pdfiks_kasuta.bat
echo %SUCCESS% Lühilink 'fotod_pdfiks_kasuta.bat' loodud.

echo.
echo ========================================
echo    Paigaldamine edukalt lõpetatud!
echo ========================================
echo.
echo Programmi käivitamiseks:
echo   Veebiliides: Topeltklikk failil "fotod_pdfiks_kasuta.bat"
echo.
echo Täpsemad kasutusjuhised: README.md
echo.

REM Küsi, kas kasutaja soovib testida programmi
set /p TEST_CHOICE=Kas soovid kohe programmi testida? (j/e): 
if /i "%TEST_CHOICE%"=="j" (
    echo %INFO% Testin programmi...
    if exist test_input.jpg (
        echo %INFO% Käivitan demo...
        call venv\Scripts\activate.bat
        python demo.py
        echo %SUCCESS% Demo test läbitud!
    ) else (
        echo %WARNING% Testpilt 'test_input.jpg' puudub, ei saa testi käivitada.
    )
)

echo.
echo Vajuta suvaline klahv väljumiseks...
pause > nul 