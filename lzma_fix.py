#!/usr/bin/env python3
"""
LZMA mooduli parandus - asendab puuduva _lzma mooduli backports.lzma-ga
"""
import sys
import importlib.util

# Kontrolli, kas _lzma moodul juba eksisteerib
if importlib.util.find_spec('_lzma') is None:
    try:
        # Proovi importida backports.lzma
        import backports.lzma
        
        # Asenda _lzma moodul backports.lzma-ga
        sys.modules['_lzma'] = backports.lzma
        print("Info: _lzma moodul asendatud backports.lzma-ga")
        
        # Nüüd peaks lzma moodul töötama korrektselt
        import lzma
        print("Info: lzma moodul edukalt laaditud")
        
    except ImportError:
        print("Hoiatus: backports.lzma pole saadaval, rembg ei pruugi töötada")
else:
    print("Info: _lzma moodul on juba olemas") 