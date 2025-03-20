#!/usr/bin/env python3
"""
Fotod PDFiks Web - Veebirakendus dokumendifotode PDF-iks konverteerimiseks

See programm pakub veebirakendust fotod_pdfiks.py programmile,
võimaldades mugavalt valida pildifaile või PDF-faile, määrata väljundfaili ja seadistada
erinevaid parameetreid. Võimalik on luua üks PDF kõigist piltidest,
eraldi PDF-id iga pildi jaoks või eraldada struktureeritud andmeid 
arvete automaatseks sisestamiseks Dolibarr'i või mõnda muusse süsteemi.
"""

import os
import sys
import subprocess
import glob
import tempfile
import shutil
import streamlit as st
from PIL import Image
import time
import importlib.util
import zipfile
import io
import json
import base64
import pandas as pd
from pdf2image import convert_from_path, convert_from_bytes
import pytesseract

# Kontrolli, kas rembg on installitud
REMBG_AVAILABLE = importlib.util.find_spec("rembg") is not None

def show_pdf(file_path):
    """Kuvab PDF-faili veebilehel sissehitatud PDF-vaaturina"""
    # Ava PDF fail
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    
    # Kasuta HTML <embed> tag'i PDF-i kuvamiseks
    pdf_display = f"""
        <embed
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="600"
            type="application/pdf"
        >
    """
    
    # Kuvamine HTML-i abil
    st.markdown(pdf_display, unsafe_allow_html=True)

def get_first_page_image(pdf_file):
    """Loob PDF-faili esimesest leheküljest pildi eelvaate jaoks"""
    try:
        # Loe PDF-faili esimene lehekülg
        images = convert_from_bytes(pdf_file.getvalue(), first_page=1, last_page=1)
        if images:
            return images[0]
        return None
    except Exception as e:
        st.error(f"PDF-faili avamisel tekkis viga: {str(e)}")
        return None

def main():
    """Streamlit rakenduse põhifunktsioon"""
    
    # Lehekülje seadistamine
    st.set_page_config(
        page_title="Fotod PDFiks",
        page_icon="📄",
        layout="wide"
    )
    
    # Päis
    st.title("Fotod PDFiks")
    st.write("Dokumendifotode ja PDF-failide konverteerimine ning andmete eraldamine")
    
    # Jaota kuva kaheks veeruks
    left_col, right_col = st.columns([2, 1])
    
    # Vasakpoolne veerg - sisend ja seaded
    with left_col:
        st.header("Sisend ja seaded")
        
        # Failide üleslaadimine
        uploaded_files = st.file_uploader(
            "Vali pildifailid või PDF-id",
            type=["jpg", "jpeg", "png", "bmp", "tiff", "tif", "pdf"],
            accept_multiple_files=True
        )
        
        # Töötlemise režiim
        processing_mode = st.radio(
            "Töötlemise režiim",
            ["Loo PDF", "Eralda andmed", "Eralda tekst", "Loo PDF ja eralda andmed"],
            index=0,
            key="processing_mode_radio"
        )
        
        # PDF-ide salvestamise režiim (ainult pildi puhul)
        if processing_mode in ["Loo PDF", "Loo PDF ja eralda andmed"]:
            # Kontrolli, kas laaditi üles pildifaile või ainult PDF-faile
            has_image_files = any([not f.name.lower().endswith('.pdf') for f in uploaded_files]) if uploaded_files else False
            
            if has_image_files:
                output_mode = st.radio(
                    "PDF loomise režiim",
                    ["Üks PDF kõigist piltidest", "Eraldi PDF iga pildi jaoks"],
                    index=0,
                    key="output_mode_radio"
                )
                
                # Väljundfaili nime seadistamine
                if output_mode == "Üks PDF kõigist piltidest":
                    default_output = "dokument.pdf"
                    output_name = st.text_input("Väljundfaili nimi", value=default_output, key="output_name_single")
                else:
                    default_output = "dokumendid.zip"
                    output_name = st.text_input("ZIP-faili nimi", value=default_output, key="output_name_multiple")
                    st.info("Eraldi PDF-id pakitakse automaatselt ZIP-faili")
            else:
                # Kui ainult PDF-failid, piisab teksti-režiimist, PDFi me ei konverteeri
                if processing_mode == "Loo PDF":
                    st.info("PDF-failid on juba PDF vormingus. Saate nendest ainult andmeid või teksti eraldada.")
        
        # Teksti eraldamise režiim
        if processing_mode == "Eralda tekst":
            with st.expander("Teksti eraldamise seaded", expanded=True):
                st.write("Pildilt või PDF-ilt eraldatakse tekst OCR abil")
                ocr_lang = st.selectbox(
                    "OCR keel", 
                    ["eng", "est", "rus", "fin", "swe", "ger", "fra"], 
                    index=1,  # Vaikimisi eesti keel
                    key="ocr_lang_text_mode"
                )
        
        # Andmete eraldamise režiim
        if processing_mode in ["Eralda andmed", "Loo PDF ja eralda andmed"]:
            with st.expander("Andmete eraldamise seaded", expanded=True):
                st.write("Pildilt või PDF-ilt eraldatakse struktureeritud andmed (arve number, kuupäev, summa jne)")
                data_format = st.radio(
                    "Andmete väljundformaat",
                    ["CSV (Dolibarr)", "JSON"],
                    index=0,
                    key="data_format_radio"
                )
                st.warning("""
                **NB!** Andmete eraldamise täpsus sõltub dokumendi kvaliteedist ja formaadist.
                Parimate tulemuste saamiseks veenduge, et dokument on hästi nähtav ja sellel on 
                selgelt eristatavad väljad.
                """)
        
        # Parameetrid
        st.subheader("Parameetrid")
        
        # DPI seaded
        dpi_values = ["150", "200", "300", "400", "600"]
        dpi = st.selectbox("DPI (lahutusvõime)", dpi_values, index=4, key="dpi_select")  # Vaikimisi 600 DPI
        
        # AI-põhine tausta eemaldamine, kui rembg on saadaval
        use_ai = False
        if REMBG_AVAILABLE:
            use_ai = st.checkbox("Kasuta AI-põhist tausta eemaldamist", value=True, key="use_ai_checkbox")
            if use_ai:
                st.success("AI-põhine tausta eemaldamine on aktiveeritud! See annab tavaliselt palju paremaid tulemusi dokumendi tuvastamisel ja tausta eemaldamisel.")
            else:
                st.info("AI-põhine tausta eemaldamine on keelatud. Kasutatakse klassikalist pilditöötlust.")
        else:
            st.warning("AI-põhine tausta eemaldamine pole saadaval. Vajalik on 'rembg' teek.")
        
        # Faili suuruse optimeerimise seaded
        optimization_options = {
            "0": "Maksimaalne kvaliteet (suur fail)",
            "1": "Kõrge kvaliteet (väiksem fail)",
            "2": "Keskmine kvaliteet (soovitatav)",
            "3": "Väike fail (madalam kvaliteet)"
        }
        optimization_level = st.selectbox(
            "PDF faili suurus",
            options=list(optimization_options.keys()),
            format_func=lambda x: optimization_options[x],
            index=2,  # Vaikimisi keskmine kvaliteet
            key="optimization_level_select"
        )
        
        # OCR seaded
        ocr_enabled = st.checkbox("OCR (teksti tuvastamine)", value=True, key="ocr_enabled_checkbox")
        
        # Keele seaded OCR-i ja andmete eraldamise jaoks
        if ocr_enabled or processing_mode in ["Eralda andmed", "Loo PDF ja eralda andmed", "Eralda tekst"]:
            lang_values = ["eng", "est", "rus", "fin", "swe", "ger", "fra"]
            lang = st.selectbox("OCR keel", lang_values, index=1, key="ocr_lang_select")  # Vaikimisi eesti keel
        
        # Debug režiim
        debug_mode = st.checkbox("Debug režiim (salvesta vaheetapid)", value=False, key="debug_mode_checkbox")
        
        # Konverteerimise nupp
        convert_button = st.button("Käivita töötlemine", key="convert_button")
    
    # Parempoolne veerg - eelvaade ja logi
    with right_col:
        st.header("Eelvaade")
        
        # Eelvaate kuvamine, kui failid on laaditud
        if uploaded_files:
            preview_file = uploaded_files[0]
            
            # Kontrolli, kas tegu on PDF-failiga
            if preview_file.name.lower().endswith('.pdf'):
                # PDF eelvaade
                temp_preview = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_preview.write(preview_file.getvalue())
                temp_preview.close()
                
                # PDF-i esimene lehekülg pildina
                first_page = get_first_page_image(preview_file)
                if first_page:
                    st.image(first_page, caption=f"{preview_file.name} (esimene lehekülg)", use_container_width=True)
                else:
                    st.warning("PDF eelvaate laadimine ebaõnnestus")
                
                # Link PDF-i vaatamiseks
                st.markdown(f"[Ava PDF-fail]({temp_preview.name})")
            else:
                # Tavalise pildi eelvaade
                st.image(preview_file, caption=preview_file.name, use_container_width=True)
            
            st.subheader("Laaditud failid")
            for file in uploaded_files:
                file_type = "PDF" if file.name.lower().endswith('.pdf') else "Pilt"
                st.write(f"- {file.name} ({file_type})")
        else:
            st.info("Lae pildifailid või PDF-id üles, et näha eelvaadet")
    
    # Progressiriba
    progress_placeholder = st.empty()
    
    # Logi ala
    if "log_content" not in st.session_state:
        st.session_state.log_content = ""
    
    log_placeholder = st.empty()
    # Näita logi ala, kui see pole tühi
    if st.session_state.log_content:
        log_placeholder.markdown(f"### Logi\n```\n{st.session_state.log_content}\n```")
    
    # Struktureeritud andmete kuvamise ala
    data_placeholder = st.empty()
    
    # Konverteerimise loogika, kui nuppu vajutatakse
    if convert_button and uploaded_files:
        # Loo ajutine kataloog failide salvestamiseks
        temp_dir = tempfile.mkdtemp()
        
        # Logi kataloogi tee
        st.session_state.log_content = f"Ajutine kataloog loodud: {temp_dir}\n"
        log_placeholder.markdown(f"### Logi\n```\n{st.session_state.log_content}\n```")
        
        try:
            # Salvesta laaditud failid
            saved_files = []
            for i, file in enumerate(uploaded_files):
                # Säilita originaalne failinimi
                original_name = os.path.splitext(file.name)[0]
                file_ext = os.path.splitext(file.name)[1]
                
                # Eralda nummerdatult ja säilita originaali nimi
                temp_filename = os.path.join(temp_dir, f"{i+1:04d}_{original_name}{file_ext}")
                
                # Salvesta fail ajutisele kettale
                with open(temp_filename, "wb") as f:
                    f.write(file.getbuffer())
                saved_files.append(temp_filename)
            
            # Seadista progress ja logi
            progress_bar = progress_placeholder.progress(0)
            
            # Alusta uut logi
            st.session_state.log_content += "Töötlemine algab...\n"
            log_placeholder.markdown(f"### Logi\n```\n{st.session_state.log_content}\n```")
            
            # Valmista ette andmete salvestamise kataloog
            data_dir = os.path.join(temp_dir, "data_output")
            os.makedirs(data_dir, exist_ok=True)
            
            # Lisa väljundfailide hoidik
            output_files = []
            data_files = []
            text_files = []
            
            # 1. Teksti eraldamine, kui seda soovitakse
            if processing_mode == "Eralda tekst":
                text_output_dir = os.path.join(temp_dir, "text_output")
                os.makedirs(text_output_dir, exist_ok=True)
                
                args = ["python", "fotod_pdfiks.py", "--input", temp_dir, "--output", text_output_dir + "/", "--text", "--lang", lang]
                
                # Lisa AI-põhine tausta eemaldamine, kui see on lubatud
                if REMBG_AVAILABLE and use_ai:
                    args.append("--use-ai")
                
                # Kuva käsurida
                st.session_state.log_content += f"Teksti eraldamine: {' '.join(args)}\n"
                log_placeholder.markdown(f"### Logi\n```\n{st.session_state.log_content}\n```")
                
                # Käivita teksti eraldamine
                process = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                # Jälgi protsessi väljundit
                for line in process.stdout:
                    line = line.strip()
                    st.session_state.log_content += line + "\n"
                    # Uuenda logi sisu samasse tekstialasse
                    log_placeholder.markdown(f"### Logi\n```\n{st.session_state.log_content}\n```")
                    
                    # Uuenda progressiriba
                    if "Teksti eraldamine:" in line:
                        try:
                            parts = line.split(":")
                            if len(parts) > 1:
                                numbers = parts[1].split("/")
                                if len(numbers) == 2:
                                    current = int(numbers[0].strip())
                                    total = int(numbers[1].split("-")[0].strip())
                                    progress = current / total
                                    progress_bar.progress(progress)
                        except:
                            pass
                
                # Oota, kuni protsess lõpetab
                return_code = process.wait()
                
                if return_code == 0:
                    # Leia kõik eraldatud tekstifailid
                    txt_paths = glob.glob(os.path.join(text_output_dir, "*.txt"))
                    
                    # Paki tekstifailid ZIP-faili
                    if txt_paths:
                        # Loo ZIP fail mälus
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            # Lisa tekstifailid
                            for txt_path in txt_paths:
                                txt_name = os.path.basename(txt_path)
                                zip_file.write(txt_path, txt_name)
                        
                        # Valmista ZIP fail allalaadimiseks
                        zip_buffer.seek(0)
                        zip_bytes = zip_buffer.getvalue()
                        
                        # Lisa failide hulka
                        text_files.append(("tekst.zip", zip_bytes, "application/zip"))
                        
                        # Näita esimese tekstifaili eelvaadet
                        if txt_paths:
                            first_txt_path = txt_paths[0]
                            with open(first_txt_path, 'r', encoding='utf-8') as f:
                                txt_content = f.read()
                            
                            with st.expander("Teksti näide", expanded=True):
                                st.text_area("Eraldatud tekst", value=txt_content, height=300, key="extracted_text_preview")
                else:
                    st.error(f"Teksti eraldamine ebaõnnestus koodiga {return_code}.")
            
            # 2. PDF-ide loomine, kui seda soovitakse JA kui on pildifaile
            if processing_mode in ["Loo PDF", "Loo PDF ja eralda andmed"] and has_image_files:
                if output_mode == "Üks PDF kõigist piltidest":
                    # Üks PDF kõigist piltidest
                    output_path = os.path.join(temp_dir, output_name)
                    args = ["python", "fotod_pdfiks.py", "--input", temp_dir, "--output", output_path, "--dpi", dpi, "--optimize", optimization_level]
                else:
                    # Eraldi PDF-id
                    output_dir = os.path.join(temp_dir, "pdf_output")
                    os.makedirs(output_dir, exist_ok=True)
                    args = ["python", "fotod_pdfiks.py", "--input", temp_dir, "--output", output_dir + "/", "--dpi", dpi, "--optimize", optimization_level, "--separate-outputs"]
                
                # Lisa OCR, kui see on lubatud
                if ocr_enabled:
                    args.append("--ocr")
                    args.extend(["--lang", lang])
                
                # Lisa AI-põhine tausta eemaldamine, kui see on lubatud
                if REMBG_AVAILABLE and use_ai:
                    args.append("--use-ai")
                
                # Lisa debug režiim, kui see on lubatud
                if debug_mode:
                    args.append("--debug")
                
                # Kuva käsurida
                st.session_state.log_content += f"PDF loomine: {' '.join(args)}\n"
                log_placeholder.markdown(f"### Logi\n```\n{st.session_state.log_content}\n```")
                
                # Käivita konverteerimine
                process = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                # Jälgi protsessi väljundit
                for line in process.stdout:
                    line = line.strip()
                    st.session_state.log_content += line + "\n"
                    # Uuenda logi sisu samasse tekstialasse
                    log_placeholder.markdown(f"### Logi\n```\n{st.session_state.log_content}\n```")
                    
                    # Uuenda progressiriba
                    if "Töötlen:" in line:
                        try:
                            parts = line.split(":")
                            if len(parts) > 1:
                                numbers = parts[1].split("/")
                                if len(numbers) == 2:
                                    current = int(numbers[0].strip())
                                    total = int(numbers[1].split("-")[0].strip())
                                    progress = current / total
                                    progress_bar.progress(progress)
                        except:
                            pass
                
                # Oota, kuni protsess lõpetab
                return_code = process.wait()
                
                if return_code == 0:
                    if output_mode == "Üks PDF kõigist piltidest":
                        # Loe loodud PDF
                        with open(output_path, "rb") as f:
                            pdf_bytes = f.read()
                        output_files.append((output_name, pdf_bytes, "application/pdf"))
                    else:
                        # Paki PDF-id ZIP-faili
                        pdf_files = glob.glob(os.path.join(output_dir, "*.pdf"))
                        txt_files = glob.glob(os.path.join(output_dir, "*.txt"))
                        
                        if pdf_files:
                            # Loo ZIP fail mälus
                            zip_buffer = io.BytesIO()
                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                for pdf_path in pdf_files:
                                    pdf_name = os.path.basename(pdf_path)
                                    zip_file.write(pdf_path, pdf_name)
                                    
                                # Lisa ka OCR tekst, kui see on olemas
                                for txt_path in txt_files:
                                    txt_name = os.path.basename(txt_path)
                                    zip_file.write(txt_path, txt_name)
                            
                            # Valmista ZIP fail allalaadimiseks
                            zip_buffer.seek(0)
                            zip_bytes = zip_buffer.getvalue()
                            output_files.append((output_name, zip_bytes, "application/zip"))
                else:
                    st.error(f"PDF loomine ebaõnnestus koodiga {return_code}.")
            
            # 3. Andmete eraldamine, kui seda soovitakse
            if processing_mode in ["Eralda andmed", "Loo PDF ja eralda andmed"]:
                # Seadista argumendid andmete eraldamiseks
                data_output_dir = os.path.join(temp_dir, "data_output")
                os.makedirs(data_output_dir, exist_ok=True)
                
                # Määra formaat
                format_arg = "csv" if data_format.startswith("CSV") else "json"
                
                args = ["python", "fotod_pdfiks.py", "--input", temp_dir, "--output", data_output_dir + "/", "--extract", "--format", format_arg, "--lang", lang]
                
                # Lisa AI-põhine tausta eemaldamine, kui see on lubatud
                if REMBG_AVAILABLE and use_ai:
                    args.append("--use-ai")
                
                # Kuva käsurida
                st.session_state.log_content += f"Andmete eraldamine: {' '.join(args)}\n"
                log_placeholder.markdown(f"### Logi\n```\n{st.session_state.log_content}\n```")
                
                # Käivita andmete eraldamine
                process = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                # Jälgi protsessi väljundit
                for line in process.stdout:
                    line = line.strip()
                    st.session_state.log_content += line + "\n"
                    # Uuenda logi sisu samasse tekstialasse
                    log_placeholder.markdown(f"### Logi\n```\n{st.session_state.log_content}\n```")
                    
                    # Uuenda progressiriba
                    if "Eraldan:" in line:
                        try:
                            parts = line.split(":")
                            if len(parts) > 1:
                                numbers = parts[1].split("/")
                                if len(numbers) == 2:
                                    current = int(numbers[0].strip())
                                    total = int(numbers[1].split("-")[0].strip())
                                    progress = current / total
                                    progress_bar.progress(progress)
                        except:
                            pass
                
                # Oota, kuni protsess lõpetab
                return_code = process.wait()
                
                if return_code == 0:
                    # Leia kõik eraldatud andmefailid
                    if format_arg == "json":
                        data_paths = glob.glob(os.path.join(data_output_dir, "*_data.json"))
                        item_paths = glob.glob(os.path.join(data_output_dir, "*_items.json"))
                    else:
                        data_paths = glob.glob(os.path.join(data_output_dir, "*_data.csv"))
                        item_paths = glob.glob(os.path.join(data_output_dir, "*_items.csv"))
                    
                    # Paki andmefailid ZIP-faili
                    if data_paths:
                        # Loo ZIP fail mälus
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                            # Lisa põhiandmed
                            for data_path in data_paths:
                                data_name = os.path.basename(data_path)
                                zip_file.write(data_path, data_name)
                            
                            # Lisa ka ridade andmed, kui need on olemas
                            for item_path in item_paths:
                                item_name = os.path.basename(item_path)
                                zip_file.write(item_path, item_name)
                        
                        # Valmista ZIP fail allalaadimiseks
                        zip_buffer.seek(0)
                        zip_bytes = zip_buffer.getvalue()
                        
                        # Määra ZIP-faili nimi
                        if format_arg == "json":
                            data_zip_name = "andmed.zip" if len(output_files) == 0 else "andmed_json.zip"
                        else:
                            data_zip_name = "andmed.zip" if len(output_files) == 0 else "andmed_csv.zip"
                        
                        data_files.append((data_zip_name, zip_bytes, "application/zip"))
                        
                        # Näita eraldatud andmete eelvaadet (esimene fail)
                        if data_paths:
                            first_data_path = data_paths[0]
                            
                            with st.expander("Eraldatud andmete näide", expanded=True):
                                if format_arg == "json":
                                    with open(first_data_path, 'r', encoding='utf-8') as f:
                                        json_data = json.load(f)
                                    
                                    # Kuva JSON-i andmed loetaval kujul
                                    st.json(json_data)
                                else:  # CSV
                                    try:
                                        df = pd.read_csv(first_data_path, delimiter=';')
                                        st.dataframe(df, key="data_preview_csv")
                                    except:
                                        st.error("CSV andmete lugemine ebaõnnestus")
                else:
                    st.error(f"Andmete eraldamine ebaõnnestus koodiga {return_code}.")
            
            # Kuva allalaadimise nupud
            progress_bar.progress(1.0)
            st.success("Töötlemine lõpetatud!")
            
            # PDF allalaadimise nupp(ud)
            for file_name, file_bytes, mime_type in output_files:
                # Näita faili suurust
                file_size_bytes = len(file_bytes)
                file_size_kb = file_size_bytes / 1024
                file_size_mb = file_size_kb / 1024
                
                if file_size_mb >= 1:
                    size_text = f"{file_size_mb:.2f} MB"
                else:
                    size_text = f"{file_size_kb:.2f} KB"
                
                st.download_button(
                    label=f"Laadi alla {file_name} ({size_text})",
                    data=file_bytes,
                    file_name=file_name,
                    mime=mime_type,
                    key=f"download_pdf_{file_name}"
                )
            
            # Andmete allalaadimise nupp(ud)
            for file_name, file_bytes, mime_type in data_files:
                # Näita faili suurust
                file_size_bytes = len(file_bytes)
                file_size_kb = file_size_bytes / 1024
                file_size_mb = file_size_kb / 1024
                
                if file_size_mb >= 1:
                    size_text = f"{file_size_mb:.2f} MB"
                else:
                    size_text = f"{file_size_kb:.2f} KB"
                
                st.download_button(
                    label=f"Laadi alla {file_name} ({size_text})",
                    data=file_bytes,
                    file_name=file_name,
                    mime=mime_type,
                    key=f"download_data_{file_name}"
                )
            
            # Teksti allalaadimise nupp(ud)
            for file_name, file_bytes, mime_type in text_files:
                # Näita faili suurust
                file_size_bytes = len(file_bytes)
                file_size_kb = file_size_bytes / 1024
                file_size_mb = file_size_kb / 1024
                
                if file_size_mb >= 1:
                    size_text = f"{file_size_mb:.2f} MB"
                else:
                    size_text = f"{file_size_kb:.2f} KB"
                
                st.download_button(
                    label=f"Laadi alla {file_name} ({size_text})",
                    data=file_bytes,
                    file_name=file_name,
                    mime=mime_type,
                    key=f"download_text_{file_name}"
                )
                
        except Exception as e:
            st.error(f"Viga: {str(e)}")
        finally:
            # Puhasta ajutised failid
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
    
    # Lisa täiendav info ja juhised
    st.markdown("---")
    with st.expander("Kuidas kasutada"):
        st.write("""
        1. Lae üles dokumendifotod või PDF-failid, mida soovid töödelda.
        2. Vali töötlemise režiim:
           - **Loo PDF**: konverteerib pildid PDF-iks
           - **Eralda andmed**: eraldab struktureeritud andmed (arve number, kuupäev, summa jne)
           - **Eralda tekst**: eraldab dokumendist kogu teksti OCR abil
           - **Loo PDF ja eralda andmed**: teeb mõlemat
        3. Seadista parameetrid vastavalt vajadusele.
        4. Klõpsa 'Käivita töötlemine' nuppu.
        5. Kui töötlemine on lõpetatud, saad tulemused alla laadida.
        
        **PDF-failide töötlemise kohta:**
        - Olemasolevate PDF-failide puhul on võimalik eraldada teksti või struktureeritud andmeid
        - Kui soovite ainult andmeid eraldada, valige "Eralda andmed" või "Eralda tekst" režiim
        """)
        
        st.warning("""
        **Andmete eraldamise kohta:**
        - Andmete eraldamise täpsus sõltub dokumendi kvaliteedist
        - Parimate tulemuste saamiseks kasuta selgeid ja hästi valgustatud pilte
        - CSV-formaadis andmed saab importida otse Dolibarr'i või Exceli tabelisse
        - Arve andmete täpseks eraldamiseks on oluline valida õige OCR keel
        """)
        
    with st.expander("Dolibarr'i importimine"):
        st.write("""
        **Kuidas importida andmeid Dolibarr'i:**
        
        1. Lae alla CSV-vormingus andmed
        2. Logi sisse Dolibarr'i
        3. Mine menüüsse: Arved > Tarnijate arved > Impordi/Ekspordi
        4. Vali CSV-fail ja seadista väljad vastavalt:
           - invoice_ref = Arve number
           - invoice_date = Arve kuupäev
           - due_date = Maksetähtaeg
           - total_ttc = Kogusumma
           - total_vat = Käibemaks
           - supplier_name = Tarnija nimi
           - supplier_vat = Tarnija reg. nr.
        5. Käivita import
        
        **Soovitused:**
        - Veendu, et importimisel on väljad õigesti seadistatud
        - Kui import ebaõnnestub, kontrolli andmeid ja vajadusel redigeeri CSV-faili
        - Puuduvate andmete korral täienda neid käsitsi Dolibarr'is
        """)


if __name__ == "__main__":
    main() 