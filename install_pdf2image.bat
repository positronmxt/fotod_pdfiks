@echo off
echo ==== pdf2image paketi paigaldus ====
echo.

REM Värvid konsooliteadete jaoks
set INFO=[INFO]
set WARNING=[HOIATUS]
set SUCCESS=[OK]
set ERROR=[VIGA]

REM Kontrolli, kas virtuaalkeskkond on olemas
if not exist venv (
    echo %ERROR% Virtuaalkeskkond puudub. Palun käivita esmalt install.bat
    pause
    exit /b 1
)

REM Aktiveeri virtuaalkeskkond
echo %INFO% Aktiveerin virtuaalkeskkonna...
call venv\Scripts\activate.bat
echo %SUCCESS% Virtuaalkeskkond aktiveeritud.

REM Kontrolli Poppler'i olemasolu
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

REM Paigalda pdf2image
echo %INFO% Paigaldan pdf2image paketi...
python -m pip install pdf2image>=1.16.0

REM Kontrolli, kas paigaldus õnnestus
python -c "import pdf2image" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo %SUCCESS% pdf2image on nüüd paigaldatud!
    echo.
    echo Käivita programm uuesti topeltklõpsates failil:
    echo "fotod_pdfiks_kasuta.bat"
    echo.
) else (
    echo %ERROR% pdf2image paigaldamine ebaõnnestus.
    pause
    exit /b 1
)

pause 