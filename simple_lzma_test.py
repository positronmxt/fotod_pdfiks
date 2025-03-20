#!/usr/bin/env python3
"""
Lihtne lzma/Python test - kontrollib Python konfiguratsiooni lzma jaoks
"""
import os
import sys
import platform
import subprocess

print("=" * 70)
print("Python ja LZMA diagnostika")
print("=" * 70)

# Python info
print(f"\nPython versioon: {platform.python_version()}")
print(f"Python asukoht: {sys.executable}")
print(f"Virtuaalkeskkond: {'Jah' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 'Ei'}")

# Kontrolli _lzma moodulit
print("\nKontrolli _lzma mooduli olemasolu:")
try:
    import _lzma
    print("OK: _lzma moodul on saadaval")
except ImportError as e:
    print(f"VIGA: _lzma moodul puudub - {e}")

# Kontrolli lzma moodulit
print("\nKontrolli lzma mooduli olemasolu:")
try:
    import lzma
    print("OK: lzma moodul on saadaval")
except ImportError as e:
    print(f"VIGA: lzma moodul puudub - {e}")

# Kontrolli süsteemi lzma teeke
print("\nKontrolli süsteemi lzma teeke:")
try:
    lzma_libs = subprocess.run(["ldconfig", "-p", "|", "grep", "liblzma"], 
                             shell=True, capture_output=True, text=True)
    if lzma_libs.stdout:
        print("OK: liblzma teegid leitud süsteemis:")
        print(lzma_libs.stdout)
    else:
        print("VIGA: liblzma teeke ei leitud süsteemis")
except Exception as e:
    print(f"Viga ldconfig käivitamisel: {e}")

# Kontrolli lzma-dev paketti
print("\nKontrolli liblzma-dev paketti:")
try:
    dpkg_query = subprocess.run(["dpkg", "-l", "liblzma-dev"], 
                              capture_output=True, text=True)
    if "ii" in dpkg_query.stdout and "liblzma-dev" in dpkg_query.stdout:
        print("OK: liblzma-dev pakett on paigaldatud:")
        for line in dpkg_query.stdout.splitlines():
            if "ii" in line and "liblzma-dev" in line:
                print(line)
    else:
        print("VIGA: liblzma-dev pakett pole paigaldatud või sellega on probleeme")
except Exception as e:
    print(f"Viga dpkg käivitamisel: {e}")

# Kontrolli PyEnv
print("\nKontrolli PyEnv konfiguratsiooni:")
try:
    pyenv_version = subprocess.run(["pyenv", "version"], 
                                 capture_output=True, text=True)
    print(f"PyEnv versioon: {pyenv_version.stdout.strip()}")
    
    # Kontrolli, kas PyEnv Python on kompileeritud lzma toega
    pyenv_prefix = subprocess.run(["pyenv", "prefix"], 
                                capture_output=True, text=True).stdout.strip()
    print(f"PyEnv Python prefix: {pyenv_prefix}")
    
    # Kontrolli, kas Python oli kompileeritud lzma toega
    config_path = os.path.join(pyenv_prefix, "lib", "python3.11", "config-3.11*", "Makefile")
    try:
        find_config = subprocess.run(f"ls {config_path}", shell=True, capture_output=True, text=True)
        config_file = find_config.stdout.strip()
        
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = f.read()
                if "HAVE_LZMA" in config:
                    print(f"OK: Python kompileeriti LZMA toega")
                else:
                    print(f"VIGA: Python kompileeriti ilma LZMA toeta")
        else:
            print(f"VIGA: Konfiguratsiooni faili ei leitud: {config_path}")
    except Exception as e:
        print(f"Viga konfiguratsiooni kontrollimisel: {e}")
        
except Exception as e:
    print(f"Viga PyEnv kontrollimisel: {e}")

# Lahendusvariandid
print("\n" + "=" * 70)
print("Võimalikud lahendused")
print("=" * 70)
print("\n1. Installige PyEnv Python uuesti koos LZMA toega:")
print("   CPPFLAGS=\"-I/usr/include\" LDFLAGS=\"-L/usr/lib\" pyenv install 3.11.6")
print("\n2. Installige backports.lzma virtuaalkeskkonda:")
print("   pip install backports.lzma")
print("\n3. Kasutage süsteemi Pythoni, mis tõenäoliselt on kompileeritud LZMA toega:")
print("   python3 -c \"import lzma; print('LZMA moodul on saadaval')\"")
print("\n4. Muutke rembg koodi, et vältida lzma kasutamist")

# Proovi installida backports.lzma
print("\nProovin installida backports.lzma automaatselt...")
try:
    subprocess.run([sys.executable, "-m", "pip", "install", "backports.lzma"], check=True)
    print("backports.lzma pakett edukalt installitud!")
    
    # Proovi importida
    try:
        import backports.lzma
        print("OK: backports.lzma moodul on edukalt imporditud")
    except ImportError as e:
        print(f"VIGA: backports.lzma importimine ebaõnnestus - {e}")
except Exception as e:
    print(f"VIGA: backports.lzma installimine ebaõnnestus - {e}") 