#!/usr/bin/env python3
"""
Debug rembg - Põhjalik diagnostikaskript rembg probleemide lahendamiseks

See skript kontrollib detailselt, miks rembg ei tööta ja proovib leida lahendusi.
"""

import os
import sys
import importlib
import platform
import subprocess
import traceback
from pathlib import Path

def print_separator(title):
    """Prindi eraldaja pealkirjaga"""
    width = 80
    print("\n" + "=" * width)
    print(f" {title} ".center(width, "="))
    print("=" * width + "\n")

def check_python_info():
    """Kuva Pythoni info"""
    print_separator("Python Info")
    print(f"Python versioon: {platform.python_version()}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path}")
    
    # Kontrolli virtuaalkeskkonda
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"Virtuaalkeskkond: Jah (prefix: {sys.prefix})")
    else:
        print("Virtuaalkeskkond: Ei")

def check_system_lzma():
    """Kontrolli süsteemi lzma teeki"""
    print_separator("Süsteemi lzma kontroll")
    try:
        # Kontrolli liblzma olemasolu süsteemis
        result = subprocess.run(["ldconfig", "-p"], capture_output=True, text=True)
        if "liblzma.so" in result.stdout:
            print("liblzma teek on süsteemis saadaval:")
            # Leia kõik liblzma soovitud read
            for line in result.stdout.splitlines():
                if "liblzma.so" in line:
                    print(f"  {line.strip()}")
        else:
            print("liblzma teek EI OLE süsteemis leitud!")
            
        # Kontrolli lzma-dev paketti
        try:
            dpkg_result = subprocess.run(["dpkg", "-l", "liblzma-dev"], capture_output=True, text=True)
            if "liblzma-dev" in dpkg_result.stdout and "ii" in dpkg_result.stdout:
                print("liblzma-dev pakett on paigaldatud")
            else:
                print("liblzma-dev pakett EI OLE paigaldatud")
        except Exception as e:
            print(f"Viga lzma-dev paketi kontrollimisel: {e}")
            
    except Exception as e:
        print(f"Viga süsteemi lzma kontrollimisel: {e}")

def check_python_lzma():
    """Kontrolli Pythoni lzma moodulit"""
    print_separator("Python lzma mooduli kontroll")
    
    # Otsi _lzma moodulit
    try:
        import _lzma
        print("_lzma moodul on saadaval!")
        print(f"_lzma faili asukoht: {_lzma.__file__}")
    except ImportError as e:
        print(f"_lzma mooduli importimine ebaõnnestus: {e}")
        
        # Vaata, kas lzma.py on olemas
        lzma_path = os.path.join(os.path.dirname(os.__file__), "lzma.py")
        if os.path.exists(lzma_path):
            print(f"lzma.py fail on olemas: {lzma_path}")
        else:
            print(f"lzma.py faili ei leitud: {lzma_path}")
        
        # Otsi _lzma.so faili
        python_lib_path = os.path.dirname(os.__file__)
        try:
            lzma_so_files = subprocess.run(
                ["find", python_lib_path, "-name", "_lzma*.so"], 
                capture_output=True, text=True
            )
            if lzma_so_files.stdout.strip():
                print("Leitud _lzma.so failid:")
                for line in lzma_so_files.stdout.splitlines():
                    print(f"  {line.strip()}")
            else:
                print(f"Ei leitud _lzma.so faile kataloogis {python_lib_path}")
        except Exception as search_error:
            print(f"_lzma.so faili otsimine ebaõnnestus: {search_error}")

def check_rembg_dependencies():
    """Kontrolli rembg sõltuvusi"""
    print_separator("rembg sõltuvuste kontroll")
    
    try:
        # Kontrolli, kas rembg on installitud
        spec = importlib.util.find_spec("rembg")
        if spec:
            print("rembg teek on installitud")
            print(f"rembg asukoht: {spec.origin}")
            
            # Proovi importida rembg
            try:
                # Osaline import ilma täieliku mooduli laadimiseta, et näha kus probleem tekib
                loader = spec.loader
                module = loader.create_module(spec)
                print("rembg mooduli loomine õnnestus")
                
                # Ürita laadida iga komponenti eraldi
                components = ["rembg.bg", "rembg.session_factory", "rembg.sessions"]
                for comp in components:
                    try:
                        importlib.import_module(comp)
                        print(f"Komponent {comp} laaditi edukalt")
                    except Exception as comp_error:
                        print(f"Viga komponendi {comp} laadimisel: {comp_error}")
                        traceback.print_exc(limit=1)
                
            except Exception as import_error:
                print(f"Viga rembg importimisel: {import_error}")
                traceback.print_exc(limit=2)
        else:
            print("rembg teek EI OLE installitud")
        
        # Kontrolli vajalikke sõltuvusi
        dependencies = [
            "numpy", "pillow", "pooch", "onnxruntime", 
            "flatbuffers", "protobuf", "sympy"
        ]
        
        print("\nVajalike sõltuvuste kontroll:")
        for dep in dependencies:
            try:
                module = importlib.import_module(dep)
                if hasattr(module, "__version__"):
                    print(f"  {dep}: OK (versioon {module.__version__})")
                else:
                    print(f"  {dep}: OK")
            except ImportError:
                print(f"  {dep}: PUUDUB")
    
    except Exception as e:
        print(f"Viga rembg sõltuvuste kontrollimisel: {e}")

def attempt_lzma_workaround():
    """Proovi leida töökorras variant lzma probleemi lahendamiseks"""
    print_separator("lzma probleemi lahendamine")
    
    # Kontrolli, kas saame lzma kasutada ilma _lzma moodulita
    print("Kontrollin, kas saame kasutada lzma moodulit standardse importimise kaudu...")
    try:
        import lzma
        print("lzma import õnnestus! See on üllatav, arvestades _lzma probleemi.")
        print(f"lzma mooduli asukoht: {lzma.__file__}")
    except ImportError as e:
        print(f"lzma importimine ebaõnnestus: {e}")
    
    # Proovi alternatiivset lahendust - pythoni-lzma pakett
    print("\nKontrollin, kas backports.lzma on saadaval...")
    try:
        import backports.lzma
        print("backports.lzma on saadaval! See võib olla alternatiivne lahendus.")
    except ImportError:
        print("backports.lzma ei ole saadaval")
        print("Võite proovida seda installida: pip install backports.lzma")
    
    # Proovi tuvastada, kas rembg saab kasutada alternatiivset pakkimismeetodit
    print("\nKontrollin, kas saame vältida lzma kasutamist rembg-s...")
    try:
        rembg_path = importlib.util.find_spec("rembg")
        if rembg_path and rembg_path.origin:
            rembg_dir = os.path.dirname(rembg_path.origin)
            pooch_imports = []
            
            for root, _, files in os.walk(rembg_dir):
                for file in files:
                    if file.endswith(".py"):
                        full_path = os.path.join(root, file)
                        with open(full_path, 'r') as f:
                            content = f.read()
                            if "pooch" in content and "lzma" in content:
                                pooch_imports.append(full_path)
            
            if pooch_imports:
                print("Leitud failid, mis kasutavad pooch ja lzma:")
                for file_path in pooch_imports:
                    print(f"  {os.path.relpath(file_path, rembg_dir)}")
                print("\nVõimalik lahendus: Muuta need failid, et vältida lzma kasutamist")
            else:
                print("Ei leitud otseseid pooch ja lzma kasutusi rembg koodis.")
    except Exception as e:
        print(f"Viga rembg koodi analüüsimisel: {e}")

def check_model_files():
    """Kontrolli, kas rembg mudelite failid on juba alla laaditud"""
    print_separator("rembg mudelite kontroll")
    
    # Tüüpilised rembg mudeli failide asukohad
    home = Path.home()
    model_paths = [
        home / ".u2net",  # Vaikimisi asukoht
        home / ".cache" / "rembg",  # Alternatiivne asukoht
    ]
    
    for path in model_paths:
        if path.exists():
            print(f"Leitud mudeli kataloog: {path}")
            models = list(path.glob("*.onnx"))
            if models:
                print("Leitud mudeli failid:")
                for model in models:
                    print(f"  {model.name} ({model.stat().st_size / (1024*1024):.1f} MB)")
            else:
                print("Mudelite kataloogi on olemas, kuid mudeleid ei leitud")
        else:
            print(f"Kataloog ei eksisteeri: {path}")
    
    # Kontrolli, kas saame alla laadida mudelid käsitsi
    print("\nMudeli käsitsi allalaadimise juhised:")
    print("1. Laadi alla u2net mudel: https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx")
    print("2. Loo kataloog ~/.u2net")
    print("3. Kopeeri allalaaditud mudel sinna")
    print("4. Proovi uuesti")

def main():
    """Põhifunktsioon"""
    print("rembg/lzma diagnostika alanud...\n")
    
    check_python_info()
    check_system_lzma()
    check_python_lzma()
    check_rembg_dependencies()
    attempt_lzma_workaround()
    check_model_files()
    
    print_separator("Kokkuvõte")
    print("Diagnostika lõpetatud!")
    print("Võimalikud lahendused:")
    print("1. Uuesti kompileerida Python lzma toega")
    print("2. Paigaldada 'backports.lzma' pakett kui eelmise punkti pole võimalik")
    print("3. Muuta rembg koodi, et vältida lzma kasutamist")
    print("4. Kasutada alternatiivset tausta eemaldamise teeki")

if __name__ == "__main__":
    main() 