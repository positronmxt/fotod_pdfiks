#!/usr/bin/env python3
"""
Kohandatud rembg test, mis püüab kasutada backports.lzma teegi 
"""
import os
import sys
import importlib.util

# Püüa importida backports.lzma
try:
    import backports.lzma
    print("backports.lzma moodul on saadaval")
    
    # Kui leidub backports.lzma, siis proovime luua mõned vajalikud 
    # sümboolsed lingid Pythoni süsteemis
    if not importlib.util.find_spec('_lzma'):
        print("Proovin luua sümboolse lingi _lzma jaoks...")
        # Leia backports.lzma asukoht
        import backports
        backports_dir = os.path.dirname(backports.__file__)
        print(f"backports.lzma asukoht: {backports_dir}")
        
        # Proovi luua sümboolne link
        try:
            # Asendame _lzma puudumise backports.lzma-ga
            _lzma_fix = """
import sys
import backports.lzma

# Asendame _lzma mooduli
sys.modules['_lzma'] = backports.lzma
            """
            # Salvesta see ajutisesse faili
            with open('_lzma_fix.py', 'w') as f:
                f.write(_lzma_fix)
            
            print("Loodud _lzma asendaja ajutine fail")
            
            # Importime selle faili, et rakendada parandus
            import _lzma_fix
            print("_lzma asendus rakendatud")
            
        except Exception as e:
            print(f"Viga _lzma asendamisel: {e}")
    
except ImportError:
    print("backports.lzma pole saadaval")
    sys.exit(1)

# Proovi importida lzma
try:
    import lzma
    print("lzma moodul on nüüd saadaval!")
except ImportError as e:
    print(f"lzma mooduli import ebaõnnestus: {e}")
    sys.exit(1)

# Nüüd proovime importida rembg
print("\nProovin importida rembg...")
try:
    import rembg
    print("rembg moodul imporditud edukalt!")
    
    # Kontrollime rembg versiooni
    import pkg_resources
    rembg_version = pkg_resources.get_distribution("rembg").version
    print(f"rembg versioon: {rembg_version}")
    
    print("\nProovin töödelda testpilti...")
    try:
        from PIL import Image
        import numpy as np
        import cv2
        
        # Loome lihtsa testpildi
        img = np.zeros((300, 300, 3), dtype=np.uint8)
        # Joonista sinine ring valgel taustal
        img.fill(255)  # Valge taust
        cv2.circle(img, (150, 150), 100, (255, 0, 0), -1)  # Sinine ring
        
        # Salvesta testpilt
        cv2.imwrite('test_input.jpg', img)
        print("Testpilt 'test_input.jpg' loodud")
        
        # Loe pilt PIL-i jaoks
        input_image = Image.open('test_input.jpg')
        
        # Töötleme pilti rembg abil
        output = rembg.remove(input_image)
        output.save('test_output.png')
        
        print("Töödeldud pilt salvestatud faili 'test_output.png'")
        print("Rembg tausta eemaldamine töötas edukalt!")
        
    except Exception as e:
        print(f"Viga testpildi töötlemisel: {e}")
        
except ImportError as e:
    print(f"Viga rembg importimisel: {e}")
    sys.exit(1)

print("\nTestimine lõppenud. Kui nägite teadet 'Rembg tausta eemaldamine töötas edukalt!', "
      "siis on rembg kasutusvalmis. Vastasel juhul vaadake veateadet ülal.") 