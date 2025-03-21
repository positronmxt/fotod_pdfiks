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

REM Kontrolli Poppler-i olemasolu (vajalik pdf2image jaoks)
echo %INFO% Kontrollin Poppler olemasolu (vajalik PDF töötlemiseks)...
where pdftoppm >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %WARNING% Poppler pole paigaldatud või pole keskkonnamuutujates.
    echo Poppler on vajalik PDF failide töötlemiseks programmis.
    echo.
    echo Palun laadi Poppler Windows'i jaoks alla ja paigalda:
    echo https://github.com/oschwartz10612/poppler-windows/releases
    echo.
    echo Pärast paigaldamist:
    echo 1. Lisa Poppler bin kataloog keskkonna Path muutujasse.
    echo 2. Käivita see skript uuesti.
    echo.
    echo Kui oled Poppler'i paigaldanud, vajuta suvaline klahv...
    pause
    
    REM Kontrolli uuesti
    where pdftoppm >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo %WARNING% Poppler pole endiselt leitav.
        echo %WARNING% Jätkame paigaldust, kuid PDF töötlemise funktsioonid ei pruugi töötada.
        echo %WARNING% Käsitsi paigaldamiseks külasta: https://github.com/oschwartz10612/poppler-windows/releases
    )
) else (
    echo %SUCCESS% Poppler leitud.
)

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

REM Paigalda setuptools eraldi ja veendu, et see on korralikult installitud
echo %INFO% Paigaldan setuptools (vajalik teiste pakettide ehitamiseks)...
python -m pip install --upgrade setuptools wheel

REM Kontrolli Python versiooni
python -c "import sys; print('Python ' + str(sys.version_info.major) + '.' + str(sys.version_info.minor))"
FOR /F "tokens=2" %%A IN ('python -c "import sys; print(str(sys.version_info.major) + '.' + str(sys.version_info.minor))"') DO set PYTHON_VERSION=%%A
echo %INFO% Python versioon: %PYTHON_VERSION%

REM Python 3.12 ja uuemate versioonide puhul on vaja erisusi
if "%PYTHON_VERSION%" == "3.12" (
    echo %INFO% Kasutan Python 3.12+ spetsiifilist paigaldusmeetodit...
    
    REM Proovi paigaldada numpy esmalt binaarfailidena
    echo %INFO% Paigaldan numpy binaarfailina...
    python -m pip install --only-binary=:all: numpy --no-build-isolation
    
    REM Paigalda OpenCV
    echo %INFO% Paigaldan OpenCV...
    python -m pip install opencv-python --no-build-isolation
    
    REM Paigalda ülejäänud paketid nimekirjast
    echo %INFO% Paigaldan ülejäänud paketid...
    for /F "tokens=*" %%A in (requirements.txt) do (
        echo %%A | findstr /v /r "^#" >nul
        if not errorlevel 1 (
            echo %%A | findstr /r "numpy opencv" >nul
            if errorlevel 1 (
                echo %INFO% Paigaldan: %%A
                python -m pip install --only-binary=:all: %%A || (
                    echo %WARNING% Ei saanud paigaldada %%A ainult binaaridega, proovin uuesti...
                    python -m pip install %%A --no-build-isolation || echo %WARNING% Paketi %%A paigaldamine ebaõnnestus.
                )
            )
        )
    )
    
    REM Kontrolli, kas streamlit on paigaldatud
    python -c "import streamlit" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo %INFO% Paigaldan Streamlit (veebiliidese jaoks)...
        python -m pip install streamlit --no-build-isolation
    )
) else (
    REM Kontrolli, kas setuptools paigaldati edukalt
    python -c "import setuptools.build_meta" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo %WARNING% setuptools.build_meta importimine ebaõnnestus. Proovin alternatiivseid meetodeid.
        
        REM Loeme requirements.txt faili ja paigaldame paketid ühekaupa
        for /F "tokens=*" %%A in (requirements.txt) do (
            echo %%A | findstr /v /r "^#" >nul
            if not errorlevel 1 (
                echo %INFO% Paigaldan paketi: %%A
                python -m pip install --no-build-isolation %%A
            )
        )
    ) else (
        REM Kui setuptools on korralikult paigaldatud, jätka tavapäraselt
        echo %INFO% Paigaldan pakette requirements.txt failist...
        python -m pip install -r requirements.txt
        if %ERRORLEVEL% NEQ 0 (
            echo %ERROR% Pythoni sõltuvuste paigaldamine ebaõnnestus.
            echo %WARNING% Proovin paigaldada pakette ühekaupa...
            
            for /F "tokens=*" %%A in (requirements.txt) do (
                echo %%A | findstr /v /r "^#" >nul
                if not errorlevel 1 (
                    echo %INFO% Paigaldan paketi: %%A
                    python -m pip install --no-build-isolation %%A
                )
            )
        )
    )
    
    REM Kontrolli, kas streamlit on paigaldatud
    python -c "import streamlit" >nul 2>&1
    if %ERRORLEVEL% NEQ 0 (
        echo %INFO% Paigaldan Streamlit (veebiliidese jaoks)...
        python -m pip install streamlit
    )
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