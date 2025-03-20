
import sys
import backports.lzma

# Asendame _lzma mooduli
sys.modules['_lzma'] = backports.lzma
            