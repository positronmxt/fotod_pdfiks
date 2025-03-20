#!/usr/bin/env python3
"""
Fotod PDFiks - Tööriist dokumentide fotode PDF-iks konverteerimiseks

See skript võimaldab dokumentidest tehtud piltide töötlemist:
- Dokumendi automaatne tuvastamine ja kärpimine fotost
- Perspektiivi korrigeerimine (dokumendi sirgestamine)
- Pildi kvaliteedi parandamine
- Üheks PDF-iks konverteerimine või iga dokument eraldi PDF-ina
- Struktureeritud andmete eraldamine dokumentidest (nt. arvetest)
- Olemasolevate PDF-failide töötlemine ja andmete eraldamine

Kasutamine:
    python fotod_pdfiks.py --input pilt.jpg --output dokument.pdf
    python fotod_pdfiks.py --input pildikaust/ --output dokument.pdf --dpi 300
    python fotod_pdfiks.py --input pilt.jpg --output dokument.pdf --optimize 3 --dpi 300
    python fotod_pdfiks.py --input pildikaust/ --output väljundkaust/ --separate-outputs --dpi 600
    python fotod_pdfiks.py --input pilt.jpg --output andmed.csv --extract --format csv
    python fotod_pdfiks.py --input dokument.pdf --output andmed.csv --extract --format csv
    python fotod_pdfiks.py --input dokument.pdf --output tekst.txt --text
"""

import os
import sys
import argparse
import glob
import json
import csv
import re
from doc_processor import DocumentProcessor


def get_image_files(input_path):
    """
    Tagasta nimekiri pildifailidest sisendtee põhjal
    
    Args:
        input_path: Sisendtee (fail või kaust)
        
    Returns:
        List pildifailide teedega
    """
    # Pildifailide laiendid
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    # PDF laiend
    pdf_extension = '.pdf'
    
    # Kui sisend on kaust, otsi kõik pildifailid
    if os.path.isdir(input_path):
        image_files = []
        # Otsi pildifailid
        for ext in image_extensions:
            glob_pattern = os.path.join(input_path, f'*{ext}')
            image_files.extend(glob.glob(glob_pattern))
            # Kontrolli ka väiketähtedega laiendeid
            glob_pattern = os.path.join(input_path, f'*{ext.upper()}')
            image_files.extend(glob.glob(glob_pattern))
        
        # Otsi PDF-failid
        glob_pattern = os.path.join(input_path, f'*{pdf_extension}')
        image_files.extend(glob.glob(glob_pattern))
        glob_pattern = os.path.join(input_path, f'*{pdf_extension.upper()}')
        image_files.extend(glob.glob(glob_pattern))
        
        # Sorteeri failid nime järgi
        image_files = sorted(image_files)
    # Kui sisend on üksik fail
    elif os.path.isfile(input_path):
        _, ext = os.path.splitext(input_path)
        if ext.lower() in image_extensions or ext.lower() == pdf_extension:
            image_files = [input_path]
        else:
            print(f"Viga: {input_path} pole toetatud pildifail või PDF.")
            sys.exit(1)
    else:
        print(f"Viga: Sisendtee {input_path} ei eksisteeri.")
        sys.exit(1)
    
    if not image_files:
        print(f"Viga: Ei leitud ühtegi pildifaili või PDF-faili teest {input_path}")
        sys.exit(1)
    
    return image_files


def create_output_dir(output_path):
    """
    Loo väljundkataloogi, kui see ei eksisteeri
    
    Args:
        output_path: Väljundtee
    """
    # Kui tee on fail, võta kataloog
    if not output_path.endswith('/'):
        output_dir = os.path.dirname(output_path)
    else:
        output_dir = output_path
        
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)


def process_single_image(processor, image_path, output_path, dpi, optimization_level, ocr=False, ocr_lang="eng", debug_dir=None):
    """
    Töötle üks pildifail ja konverteeri see PDF-iks
    
    Args:
        processor: DocumentProcessor instants
        image_path: Pildi tee
        output_path: Väljund PDF-i tee
        dpi: Pildi resolutsioon punktides tolli kohta
        optimization_level: Optimeerimise tase
        ocr: Kas teha OCR
        ocr_lang: OCR keel
        debug_dir: Debug väljundkaust
    """
    # Töötle pilti
    processor.process_image(image_path, output_dir=debug_dir, optimization_level=optimization_level)
    
    # Konverteeri PDF-iks
    processor.convert_to_pdf([image_path], output_path, dpi=dpi, optimization_level=optimization_level)
    print(f"PDF loodud: {output_path}")
    
    # OCR töötlus, kui soovitud
    if ocr:
        text = processor.ocr_document(image_path, lang=ocr_lang)
        
        # Salvesta OCR tulemus tekstifaili
        text_path = os.path.splitext(output_path)[0] + '.txt'
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"OCR tulemus salvestatud: {text_path}")


def extract_structured_data(processor, image_path, output_format, lang):
    """
    Eralda struktureeritud andmed dokumendist ja salvesta need vastavalt formaadile
    
    Args:
        processor: DocumentProcessor instants
        image_path: Pildi või PDF-faili tee
        output_format: Väljundformaat (json või csv)
        lang: OCR keele kood
    
    Returns:
        str: Väljundfaili tee
    """
    # Kontrolli, kas tegu on PDF-failiga
    if image_path.lower().endswith('.pdf'):
        # Eralda andmed PDF-failist
        data = processor.extract_structured_data_from_pdf(image_path, lang=lang)
    else:
        # Eralda andmed pildifailist
        data = processor.extract_structured_data(image_path, lang=lang)
    
    # Määrame väljundfaili nime
    basename = os.path.splitext(os.path.basename(image_path))[0]
    
    if output_format == 'json':
        # JSON väljund
        output_path = f"{basename}_data.json"
        processor.export_invoice_data_to_json(data, output_path)
    else:
        # CSV väljund
        output_path = f"{basename}_data.csv"
        processor.export_invoice_data_to_csv(data, output_path)
    
    return output_path


def extract_text(processor, image_path, output_path, lang):
    """
    Eralda tekst dokumendist OCR abil ja salvesta tekstifaili
    
    Args:
        processor: DocumentProcessor instants
        image_path: Pildi või PDF-faili tee
        output_path: Väljundfaili tee
        lang: OCR keele kood
        
    Returns:
        str: OCR tulemus (tekst)
    """
    print(f"Eraldan teksti failist: {image_path}")
    
    # Kontrolli, kas tegu on PDF-failiga
    if image_path.lower().endswith('.pdf'):
        # Eralda tekst PDF-failist
        text = processor.extract_text_from_pdf(image_path, lang=lang)
    else:
        # Eralda tekst pildifailist
        text = processor.ocr_document(image_path, lang=lang)
    
    # Salvesta tulemus tekstifaili
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Tekst salvestatud: {output_path}")
    
    return text


def main():
    """Põhifunktsioon"""
    # Argumendid käsurealt
    parser = argparse.ArgumentParser(description='Konverdi dokumendifotod PDF-iks')
    parser.add_argument('--input', required=True, help='Sisendfail või -kaust piltide või PDF-idega')
    parser.add_argument('--output', required=True, help='Väljund PDF-fail või kaust (--separate-outputs korral)')
    parser.add_argument('--dpi', type=int, default=300, help='Väljund-PDF resolutsioon (vaikimisi 300)')
    parser.add_argument('--debug', action='store_true', help='Luba debug režiim')
    parser.add_argument('--ocr', action='store_true', help='Tuvasta tekst (OCR)')
    parser.add_argument('--text', action='store_true', help='Eralda tekst dokumendist ja salvesta tekstifaili')
    parser.add_argument('--lang', default='est', help='OCR keele kood (vaikimisi: est)')
    parser.add_argument('--optimize', type=int, default=2, choices=[0, 1, 2, 3], 
                        help='Optimeerimise tase: 0=max kvaliteet, 3=min suurus (vaikimisi: 2)')
    parser.add_argument('--use-ai', action='store_true', help='Kasuta AI-põhist tausta eemaldamist (kui rembg on installitud)')
    parser.add_argument('--separate-outputs', action='store_true',
                        help='Töötle iga sisendfail eraldi PDF-iks (--output peab siis olema kaust)')
    parser.add_argument('--extract', action='store_true', help='Eralda struktureeritud andmed dokumentidest')
    parser.add_argument('--format', default='json', choices=['json', 'csv'], help='Struktureeritud andmete väljundformaat')
    
    args = parser.parse_args()
    
    # Optimeerimistaseme kirjeldused
    optimization_descriptions = {
        0: "maksimaalse kvaliteediga",
        1: "kõrge kvaliteediga",
        2: "keskmise kvaliteediga",
        3: "väikese failisuurusega"
    }
    
    print(f"Optimeerimistase: {args.optimize} ({optimization_descriptions[args.optimize]})")
    
    # Kui kasutatakse separate-outputs, siis output peab olema kaust
    if args.separate_outputs:
        if not args.output.endswith('/') and not os.path.isdir(args.output):
            # Lisa lõppu '/', et luua vajadusel kataloog
            args.output = args.output + '/'
            print(f"Eraldi väljundite režiim: Väljund suunatakse kataloogi {args.output}")
    
    # Loo töötleja
    processor = DocumentProcessor(debug=args.debug, use_ai=args.use_ai)
    
    # Leia pildifailid
    image_files = get_image_files(args.input)
    print(f"Leitud {len(image_files)} pildifaili töötlemiseks")
    
    # Loo väljundkaust
    create_output_dir(args.output)
    
    # Debug režiimi korral loo kaust vaheetappide salvestamiseks
    debug_dir = None
    if args.debug:
        if args.separate_outputs:
            debug_dir = os.path.join(args.output, 'debug')
        else:
            debug_dir = os.path.splitext(args.output)[0] + '_debug'
        os.makedirs(debug_dir, exist_ok=True)
    
    # Kui tahetakse ainult andmeid eraldada, siis teeme seda
    if args.extract:
        print(f"Eraldan struktureeritud andmed dokumentidest...")
        
        # Kontrolli, et väljundkaust oleks olemas
        output_dir = args.output
        if not output_dir.endswith('/') and os.path.splitext(output_dir)[1] not in ['.json', '.csv']:
            output_dir = output_dir + '/'
        create_output_dir(output_dir)
        
        # Töötleme iga faili eraldi
        for i, image_path in enumerate(image_files):
            basename = os.path.splitext(os.path.basename(image_path))[0]
            
            # Väljundfaili teekond
            if output_dir.endswith('/'):
                if args.format == 'json':
                    output_path = os.path.join(output_dir, f"{basename}_data.json")
                else:
                    output_path = os.path.join(output_dir, f"{basename}_data.csv")
            else:
                output_path = args.output
            
            print(f"Eraldan: {i+1}/{len(image_files)} - {os.path.basename(image_path)} -> {output_path}")
            
            # Eralda andmed
            if image_path.lower().endswith('.pdf'):
                data = processor.extract_structured_data_from_pdf(image_path, lang=args.lang)
            else:
                data = processor.extract_structured_data(image_path, lang=args.lang)
            
            # Salvesta vastavalt formaadile
            if args.format == 'json':
                processor.export_invoice_data_to_json(data, output_path)
                print(f"JSON andmed eraldatud ja salvestatud: {output_path}")
            else:
                processor.export_invoice_data_to_csv(data, output_path)
                print(f"CSV andmed eraldatud ja salvestatud: {output_path}")
            
            # Kui leiti arveread, oleme ka neist teada
            items_path = os.path.splitext(output_path)[0] + "_items." + args.format
            if os.path.exists(items_path):
                print(f"Arve elementide andmed salvestatud: {items_path}")
        
        print(f"Andmete eraldamine lõpetatud!")
        return
    
    # Kui tahetakse ainult teksti eraldada, siis teeme seda
    if args.text:
        print(f"Eraldan teksti dokumentidest...")
        
        # Üksiku faili töötlemine
        if len(image_files) == 1 and not os.path.isdir(args.output):
            # Eralda tekst
            extract_text(processor, image_files[0], args.output, args.lang)
        else:
            # Mitme faili töötlemine - väljund peab olema kaust
            output_dir = args.output
            if not output_dir.endswith('/'):
                output_dir = output_dir + '/'
            create_output_dir(output_dir)
            
            # Töötleme iga faili eraldi
            for i, image_path in enumerate(image_files):
                basename = os.path.splitext(os.path.basename(image_path))[0]
                output_path = os.path.join(output_dir, f"{basename}.txt")
                
                print(f"Teksti eraldamine: {i+1}/{len(image_files)} - {os.path.basename(image_path)} -> {output_path}")
                extract_text(processor, image_path, output_path, args.lang)
            
            print(f"Teksti eraldamine lõpetatud!")
        return
    
    # Töötleme pildid eraldi või üheks PDF-iks
    if args.separate_outputs:
        # Töötleme iga pildi eraldi PDF-iks
        for i, image_path in enumerate(image_files):
            basename = os.path.splitext(os.path.basename(image_path))[0]
            output_path = os.path.join(args.output, f"{basename}.pdf")
            
            print(f"Töötlen: {i+1}/{len(image_files)} - {os.path.basename(image_path)} -> {output_path}")
            
            # Töötle üks pilt
            process_single_image(
                processor, 
                image_path, 
                output_path, 
                args.dpi, 
                args.optimize, 
                ocr=args.ocr, 
                ocr_lang=args.lang, 
                debug_dir=debug_dir
            )
            
        print(f"Töötlemine lõpetatud. {len(image_files)} PDF-i loodud kataloogis {args.output}")
    else:
        # OCR töötlus, kui soovitud (teostame enne PDF loomist)
        if args.ocr:
            for i, image_path in enumerate(image_files):
                print(f"OCR töötlus: {i+1}/{len(image_files)} - {os.path.basename(image_path)}")
                text = processor.ocr_document(image_path, lang=args.lang)
                
                # Salvesta OCR tulemus tekstifaili
                text_file = os.path.splitext(os.path.basename(image_path))[0] + '.txt'
                text_path = os.path.join(os.path.dirname(args.output), text_file)
                with open(text_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"OCR tulemus salvestatud: {text_path}")
        
        # Konverteeri PDF-iks
        print(f"Konverteerin pilte üheks PDF-iks")
        for i, image_path in enumerate(image_files):
            print(f"Töötlen: {i+1}/{len(image_files)} - {os.path.basename(image_path)}")
            # Vahetöötluse etapid salvestatakse debug_dir-i, kui debug režiim on lubatud
            processor.process_image(image_path, output_dir=debug_dir, optimization_level=args.optimize)
        
        # Konverteeri kõik töödeldud pildid üheks PDF-iks
        processor.convert_to_pdf(image_files, args.output, dpi=args.dpi, optimization_level=args.optimize)
        print(f"PDF loodud: {args.output}")


if __name__ == '__main__':
    main() 