#!/usr/bin/env python3
"""
Lihtne rembg test - kasutab ainult PIL library'd
"""
import os
import sys
import importlib.util
from PIL import Image

# Kontrolli, kas rembg on installitud
REMBG_INSTALLED = importlib.util.find_spec("rembg") is not None
if not REMBG_INSTALLED:
    print("Viga: rembg teek pole installitud!")
    print("Palun installige see käsuga: pip install rembg")
    sys.exit(1)

# Proovi importida rembg
try:
    import rembg
    print("rembg teek edukalt laaditud!")
except ImportError as e:
    print(f"Viga rembg teegi laadimisel: {e}")
    sys.exit(1)

# Test parameetrid
INPUT_FILE = "piltsisse/IMG_20241202_122830_214.jpg"
OUTPUT_FILE = "test_transparent.png"

print(f"Testin rembg teegi põhifunktsionaalsust")
print(f"Sisend: {INPUT_FILE}")
print(f"Väljund: {OUTPUT_FILE}")

try:
    # Loe sisendpilt
    if not os.path.exists(INPUT_FILE):
        print(f"Viga: Sisendfaili {INPUT_FILE} ei leitud!")
        sys.exit(1)
        
    input_image = Image.open(INPUT_FILE)
    print(f"Pilt loetud, suurus: {input_image.size}")
    
    # Eemalda taust
    print("Eemaldan tausta AI abil...")
    output = rembg.remove(input_image)
    
    # Salvesta tulemus
    output.save(OUTPUT_FILE)
    print(f"Tulemus salvestatud: {OUTPUT_FILE}")
    print("Test edukalt lõpetatud!")
    
except Exception as e:
    print(f"Viga testi käigus: {e}")
    sys.exit(1) 