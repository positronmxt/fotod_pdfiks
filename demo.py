#!/usr/bin/env python3
"""
Fotod PDFiks Demo - Näidisprogramm põhifunktsionaalsuse demonstreerimiseks

See skript näitab, kuidas kasutada DocumentProcessor klassi oma programmis.
"""

import os
from doc_processor import DocumentProcessor

def main():
    """Demo põhifunktsioon"""
    print("Fotod PDFiks Demo")
    print("=================")
    
    # Loo DocumentProcessor objekt debug režiimis
    processor = DocumentProcessor(debug=True)
    
    # Demo kaust
    demo_dir = "demo_output"
    os.makedirs(demo_dir, exist_ok=True)
    
    # Kontrolli, kas kasutajal on pildid
    print("\nKasutamiseks:")
    print("1. Pane mõned dokumendifotod sellesse kausta")
    print("2. Jooksuta seda skripti uuesti")
    print("3. Vaata tulemusi demo_output kaustas")
    
    # Otsi pildifaile praeguses kaustas
    image_extensions = ['.jpg', '.jpeg', '.png']
    image_files = []
    
    for ext in image_extensions:
        for file in os.listdir('.'):
            if file.lower().endswith(ext):
                image_files.append(file)
    
    if not image_files:
        print("\nEi leidnud ühtegi pildifaili. Palun lisa mõned pildid kausta.")
        return
    
    print(f"\nLeitud {len(image_files)} pildifaili. Töötlen neid...")
    
    # Töötle iga pilti ja salvesta debug pildid
    for i, image_file in enumerate(image_files):
        print(f"\nTöötlen pilti {i+1}/{len(image_files)}: {image_file}")
        
        # Loo debug kaust selle pildi jaoks
        image_debug_dir = os.path.join(demo_dir, f"debug_{os.path.splitext(image_file)[0]}")
        os.makedirs(image_debug_dir, exist_ok=True)
        
        # Töötle pilti ja salvesta vaheetapid
        processor.process_image(image_file, output_dir=image_debug_dir)
        
        # Kui soovid OCR teksti tuvastada
        try:
            text = processor.ocr_document(image_file)
            text_file = os.path.join(demo_dir, f"{os.path.splitext(image_file)[0]}_text.txt")
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"OCR tulemus salvestatud: {text_file}")
        except Exception as e:
            print(f"OCR ebaõnnestus: {e}")
    
    # Loo PDF kõigist piltidest
    output_pdf = os.path.join(demo_dir, "dokumendid.pdf")
    print(f"\nLoon PDF-i kõigist piltidest: {output_pdf}")
    processor.convert_to_pdf(image_files, output_pdf)
    
    # Loo PDF-id igast pildist eraldi
    for image_file in image_files:
        output_pdf = os.path.join(demo_dir, f"{os.path.splitext(image_file)[0]}.pdf")
        print(f"Loon PDF-i pildist {image_file}: {output_pdf}")
        processor.convert_to_pdf([image_file], output_pdf)
    
    print("\nDemo lõppenud! Vaata tulemusi demo_output kaustas.")
    print("Dokumendi töötlemise vaheetapid on nähtavad debug_ kaustades.")

if __name__ == "__main__":
    main() 