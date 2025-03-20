#!/usr/bin/env python3
"""
Fotod PDFiks GUI - Graafiline kasutajaliides dokumendifotode PDF-iks konverteerimiseks

See programm pakub graafilist kasutajaliidest fotod_pdfiks.py programmile,
võimaldades mugavalt valida pildifaile, määrata väljundfaili ja seadistada
erinevaid parameetreid.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import glob
from PIL import Image, ImageTk
import time

class RedirectText:
    """Klassi väljundi suunamiseks Tkinter teksti vidžetisse"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""

    def write(self, string):
        self.buffer += string
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)
        
    def flush(self):
        pass

class FotodPdfiksGUI:
    """Fotod PDFiks programmi graafiline kasutajaliides"""
    def __init__(self, root):
        self.root = root
        self.root.title("Fotod PDFiks")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Pildifailide nimekiri
        self.image_files = []
        
        # GUI loomine
        self.create_widgets()
        
        # Drag-and-drop toetus
        self.setup_drag_drop()
        
        # Määra ikooni (kui võimalik)
        try:
            # Loo väike ikooni pilt PDF ikooniga
            self.root.iconbitmap("icon.ico")
        except:
            pass
    
    def create_widgets(self):
        """Loo kõik vajalikud vidžetid"""
        # Peamine raamistik
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Vasakpoolne paneel - sisend ja parameetrid
        left_frame = ttk.LabelFrame(main_frame, text="Sisend ja seaded", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Parempoolne paneel - fail preview ja logi
        right_frame = ttk.LabelFrame(main_frame, text="Eelvaade ja logi", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Sisendpaneeli elemendid
        # 1. Pildifailide valimine
        input_frame = ttk.Frame(left_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(input_frame, text="Sisend:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.input_var = tk.StringVar()
        input_entry = ttk.Entry(input_frame, textvariable=self.input_var, width=30)
        input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(input_frame, text="Vali failid", command=self.browse_input_files).pack(side=tk.LEFT)
        ttk.Button(input_frame, text="Vali kaust", command=self.browse_input_dir).pack(side=tk.LEFT, padx=(5, 0))
        
        # 2. Väljundfaili valimine
        output_frame = ttk.Frame(left_frame)
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(output_frame, text="Väljund:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.output_var = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var, width=30)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(output_frame, text="Vali fail", command=self.browse_output_file).pack(side=tk.LEFT)
        
        # 3. Parameetrid
        params_frame = ttk.LabelFrame(left_frame, text="Parameetrid", padding="10")
        params_frame.pack(fill=tk.X, pady=(0, 10))
        
        # DPI seaded
        dpi_frame = ttk.Frame(params_frame)
        dpi_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(dpi_frame, text="DPI:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.dpi_var = tk.StringVar(value="300")
        dpi_values = ["150", "200", "300", "400", "600"]
        dpi_combo = ttk.Combobox(dpi_frame, textvariable=self.dpi_var, values=dpi_values, width=5)
        dpi_combo.pack(side=tk.LEFT)
        
        # OCR seaded
        ocr_frame = ttk.Frame(params_frame)
        ocr_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.ocr_var = tk.BooleanVar(value=False)
        ocr_check = ttk.Checkbutton(ocr_frame, text="OCR (teksti tuvastamine)", variable=self.ocr_var)
        ocr_check.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Label(ocr_frame, text="Keel:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.lang_var = tk.StringVar(value="eng")
        lang_values = ["eng", "est", "rus", "fin", "swe", "ger", "fra"]
        lang_combo = ttk.Combobox(ocr_frame, textvariable=self.lang_var, values=lang_values, width=5)
        lang_combo.pack(side=tk.LEFT)
        
        # Debug režiim
        debug_frame = ttk.Frame(params_frame)
        debug_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.debug_var = tk.BooleanVar(value=False)
        debug_check = ttk.Checkbutton(debug_frame, text="Debug režiim (salvesta vaheetapid)", variable=self.debug_var)
        debug_check.pack(side=tk.LEFT)
        
        # 4. Failide nimekiri
        files_frame = ttk.LabelFrame(left_frame, text="Failide nimekiri", padding="10")
        files_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar failide nimekirjale
        scrollbar = ttk.Scrollbar(files_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.files_listbox = tk.Listbox(files_frame, selectmode=tk.EXTENDED, yscrollcommand=scrollbar.set)
        self.files_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.files_listbox.yview)
        
        # 5. Toimingute nupud
        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(buttons_frame, text="Eemalda valitud", command=self.remove_selected_files).pack(side=tk.LEFT)
        ttk.Button(buttons_frame, text="Puhasta nimekiri", command=self.clear_files).pack(side=tk.LEFT, padx=(5, 0))
        
        # Käivitamise nupp
        convert_button = ttk.Button(left_frame, text="Konverteeri PDF-iks", command=self.start_conversion)
        convert_button.pack(fill=tk.X, pady=(10, 0))
        
        # Parempoolse paneeli elemendid
        # 1. Eelvaade
        preview_frame = ttk.LabelFrame(right_frame, text="Eelvaade", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.preview_label = ttk.Label(preview_frame, text="Vali fail eelvaateks")
        self.preview_label.pack(fill=tk.BOTH, expand=True)
        
        # 2. Logi
        log_frame = ttk.LabelFrame(right_frame, text="Logi", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar logile
        log_scrollbar = ttk.Scrollbar(log_frame)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, wrap=tk.WORD, height=10, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scrollbar.config(command=self.log_text.yview)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        # Progressiriba
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(10, 0))
        
        # Oleku silt
        self.status_var = tk.StringVar(value="Valmis")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(fill=tk.X, pady=(5, 0))
        
        # Suuna standardväljund logi tekstialale
        self.stdout_redirect = RedirectText(self.log_text)
        sys.stdout = self.stdout_redirect
        
        # Lisa eelvaate funktsionaalsus failide nimekirjale
        self.files_listbox.bind('<<ListboxSelect>>', self.show_preview)
    
    def setup_drag_drop(self):
        """Seadista drag-and-drop funktsionaalsus"""
        # Kui platvormi toetus on olemas
        try:
            self.root.drop_target_register(tk.DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.handle_drop)
        except:
            print("Drag-and-drop pole selles keskkonnas toetatud.")
    
    def handle_drop(self, event):
        """Käsitle failide lohistamist aknasse"""
        # Parsi lohistatud failide tee
        files = event.data
        
        # Platvormist sõltuvalt võib olla erinevalt vormindatud
        if "{" in files:
            files = files.replace("{", "").replace("}", "")
            
        if isinstance(files, str):
            files = files.split()
        
        for file in files:
            file = file.strip()
            # Eemalda võimalikud jutumärgid
            if file.startswith('"') and file.endswith('"'):
                file = file[1:-1]
            
            # Kontrolli, kas fail või kaust eksisteerib
            if os.path.exists(file):
                if os.path.isdir(file):
                    self.add_directory(file)
                else:
                    self.add_file(file)
    
    def browse_input_files(self):
        """Ava failivalija pildifailide valimiseks"""
        filetypes = [
            ("Pildifailid", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif"),
            ("JPEG failid", "*.jpg *.jpeg"),
            ("PNG failid", "*.png"),
            ("Kõik failid", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Vali pildifailid",
            filetypes=filetypes
        )
        
        if files:
            # Lisa valitud failid nimekirja
            for file in files:
                self.add_file(file)
            
            # Uuenda sisendivälja
            if len(files) == 1:
                self.input_var.set(files[0])
            else:
                self.input_var.set(f"{len(files)} faili valitud")
    
    def browse_input_dir(self):
        """Ava kaustavalija piltide kausta valimiseks"""
        directory = filedialog.askdirectory(
            title="Vali piltide kaust"
        )
        
        if directory:
            self.add_directory(directory)
            self.input_var.set(directory)
    
    def add_directory(self, directory):
        """Lisa kõik pildifailid kaustast"""
        # Pildifailide laiendid
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
        
        # Otsi kõik pildifailid
        files = []
        for ext in image_extensions:
            glob_pattern = os.path.join(directory, f'*{ext}')
            files.extend(glob.glob(glob_pattern))
            # Kontrolli ka suurtähtedega laiendeid
            glob_pattern = os.path.join(directory, f'*{ext.upper()}')
            files.extend(glob.glob(glob_pattern))
        
        # Sorteeri failid nime järgi
        files = sorted(files)
        
        # Lisa nimekirja
        for file in files:
            self.add_file(file)
        
        print(f"Lisatud {len(files)} faili kaustast '{directory}'")
    
    def add_file(self, file_path):
        """Lisa fail pildifailide nimekirja"""
        # Kontrolli, kas fail on pildifail
        ext = os.path.splitext(file_path)[1].lower()
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
        
        if ext not in valid_extensions:
            print(f"Hoiatus: '{file_path}' pole toetatud pildifail ja jäetakse vahele.")
            return
        
        # Kontrolli, kas fail on juba nimekirjas
        if file_path in self.image_files:
            print(f"Hoiatus: '{file_path}' on juba nimekirjas.")
            return
        
        # Lisa fail nimekirja
        self.image_files.append(file_path)
        self.files_listbox.insert(tk.END, os.path.basename(file_path))
        
        # Paku välja vaikimisi väljundfail esimese faili põhjal
        if len(self.image_files) == 1 and not self.output_var.get():
            output_dir = os.path.dirname(file_path)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            self.output_var.set(os.path.join(output_dir, f"{base_name}.pdf"))
    
    def browse_output_file(self):
        """Ava failivalija väljundfaili valimiseks"""
        filetypes = [
            ("PDF failid", "*.pdf"),
            ("Kõik failid", "*.*")
        ]
        
        file = filedialog.asksaveasfilename(
            title="Salvesta PDF",
            filetypes=filetypes,
            defaultextension=".pdf"
        )
        
        if file:
            self.output_var.set(file)
    
    def remove_selected_files(self):
        """Eemalda valitud failid nimekirjast"""
        selected_indices = self.files_listbox.curselection()
        
        # Eemalda tagantpoolt, et indeksid ei muutuks
        for i in sorted(selected_indices, reverse=True):
            del self.image_files[i]
            self.files_listbox.delete(i)
    
    def clear_files(self):
        """Puhasta failide nimekiri"""
        self.image_files = []
        self.files_listbox.delete(0, tk.END)
    
    def show_preview(self, event):
        """Näita valitud faili eelvaadet"""
        # Kontrolli, kas midagi on valitud
        selection = self.files_listbox.curselection()
        if not selection:
            return
        
        # Võta valitud fail
        index = selection[0]
        if index < 0 or index >= len(self.image_files):
            return
        
        file_path = self.image_files[index]
        
        try:
            # Ava pilt
            img = Image.open(file_path)
            
            # Muuda pildi suurus, et see mahuks eelvaate alasse
            preview_width = 300
            preview_height = 400
            
            # Arvuta uus suurus, säilitades pildi suhte
            width, height = img.size
            ratio = min(preview_width / width, preview_height / height)
            new_size = (int(width * ratio), int(height * ratio))
            
            # Muuda pildi suurus
            img = img.resize(new_size, Image.LANCZOS)
            
            # Konverdi Tkinter PhotoImage objektiks
            photo = ImageTk.PhotoImage(img)
            
            # Uuenda eelvaate silti
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo  # Hoia viidet, et vältida prügikogumist
        except Exception as e:
            self.preview_label.config(image="", text=f"Viga pildi laadimisel:\n{str(e)}")
    
    def start_conversion(self):
        """Alusta konverteerimist eraldi lõimes"""
        # Kontrolli, kas sisendid on korrektsed
        if not self.image_files:
            messagebox.showerror("Viga", "Palun vali vähemalt üks pildifail.")
            return
        
        if not self.output_var.get():
            messagebox.showerror("Viga", "Palun määra väljund PDF-fail.")
            return
        
        # Alusta konverteerimist eraldi lõimes
        thread = threading.Thread(target=self.convert_to_pdf)
        thread.daemon = True
        thread.start()
    
    def convert_to_pdf(self):
        """Konverteeri pildid PDF-iks"""
        try:
            # Seadista UI olekud
            self.status_var.set("Konverteerimine...")
            self.progress_var.set(0)
            self.root.update_idletasks()
            
            # Valmista ette argumendid
            python_executable = "python"
            args = [python_executable, "fotod_pdfiks.py"]
            
            # Kui on ainult üks fail, kasuta seda otseselt
            if len(self.image_files) == 1:
                args.extend(["--input", self.image_files[0]])
            else:
                # Loome ajutise kausta mitme faili jaoks
                tmp_dir = os.path.join(os.path.dirname(self.output_var.get()), ".tmp_fotod")
                os.makedirs(tmp_dir, exist_ok=True)
                
                # Kopeeri failid sinna korrektsete nimedega järjestuse tagamiseks
                for i, file in enumerate(self.image_files):
                    ext = os.path.splitext(file)[1]
                    # Kasuta nullidega täidetud numbreid, et tagada korrektne sorteerimine
                    new_name = f"{i+1:04d}{ext}"
                    new_path = os.path.join(tmp_dir, new_name)
                    
                    # Kasuta kopeerimist, et säilitada originaalfailid
                    import shutil
                    shutil.copy2(file, new_path)
                
                args.extend(["--input", tmp_dir])
            
            # Lisa väljund
            args.extend(["--output", self.output_var.get()])
            
            # Lisa DPI
            if self.dpi_var.get():
                args.extend(["--dpi", self.dpi_var.get()])
            
            # Lisa OCR, kui see on lubatud
            if self.ocr_var.get():
                args.append("--ocr")
                if self.lang_var.get():
                    args.extend(["--lang", self.lang_var.get()])
            
            # Lisa debug režiim, kui see on lubatud
            if self.debug_var.get():
                args.append("--debug")
            
            print(f"Käivitan: {' '.join(args)}")
            
            # Käivita konverteerimine
            env = os.environ.copy()
            # Tühista keskkonna muutujad
            if "PYTHONHOME" in env:
                del env["PYTHONHOME"]
            if "PYTHONPATH" in env:
                del env["PYTHONPATH"]
            
            process = subprocess.Popen(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                env=env,
                shell=False
            )
            
            # Jälgi protsessi väljundit
            log_output = []
            for line in process.stdout:
                # Uuenda progressiriba, kui see sisaldab edenemise infot
                if "Töötlen:" in line:
                    try:
                        # Analüüsi rida, et saada praegune ja kogu failide arv
                        parts = line.split(":")
                        if len(parts) > 1:
                            numbers = parts[1].split("/")
                            if len(numbers) == 2:
                                current = int(numbers[0].strip())
                                total = int(numbers[1].split("-")[0].strip())
                                progress = (current / total) * 100
                                self.progress_var.set(progress)
                                self.root.update_idletasks()
                    except:
                        pass
                
                # Logi väljund
                log_line = line.strip()
                log_output.append(log_line)
                print(log_line)
                
                # Uuenda logi ala, kui see on olemas
                if hasattr(self, 'log_text') and self.log_text:
                    self.log_text.config(state=tk.NORMAL)
                    self.log_text.insert(tk.END, log_line + "\n")
                    self.log_text.see(tk.END)
                    self.log_text.config(state=tk.DISABLED)
                    self.root.update_idletasks()
            
            # Oota, kuni protsess lõpetab
            return_code = process.wait()
            
            # Kustuta ajutine kaust, kui see loodi
            if len(self.image_files) > 1 and os.path.exists(tmp_dir):
                import shutil
                shutil.rmtree(tmp_dir)
            
            # Kontrolli, kas konverteerimine õnnestus
            if return_code == 0:
                self.status_var.set("Konverteerimine õnnestus!")
                self.progress_var.set(100)
                
                # Küsi, kas kasutaja soovib avada PDF-i
                if messagebox.askyesno("Konverteerimine lõppenud", 
                                      f"PDF on loodud: {self.output_var.get()}\n\nKas soovid seda avada?"):
                    self.open_pdf()
            else:
                self.status_var.set("Konverteerimine ebaõnnestus!")
                error_message = f"Konverteerimine ebaõnnestus koodiga {return_code}.\n\n"
                error_message += "Veateade võib olla logi alas. Kontrolli järgmist:\n"
                error_message += "1. Kas pildifail on korrektne ja loetav?\n"
                error_message += "2. Kas väljundkataloog eksisteerib ja on kirjutatav?\n"
                error_message += "3. Kui OCR on lubatud, kas Tesseract on õigesti installitud?"
                messagebox.showerror("Viga", error_message)
        
        except Exception as e:
            self.status_var.set("Viga!")
            messagebox.showerror("Viga", str(e))
            print(f"Viga: {str(e)}")
    
    def open_pdf(self):
        """Ava loodud PDF-fail süsteemi vaikeprogrammiga"""
        pdf_path = self.output_var.get()
        
        if not os.path.exists(pdf_path):
            messagebox.showerror("Viga", f"Faili ei leitud: {pdf_path}")
            return
        
        try:
            # Kasuta platvormi-spetsiifilist käsku
            if sys.platform == 'win32':
                os.startfile(pdf_path)
            elif sys.platform == 'darwin':  # macOS
                subprocess.call(['open', pdf_path])
            else:  # Linux
                subprocess.call(['xdg-open', pdf_path])
        except Exception as e:
            messagebox.showerror("Viga", f"PDF-i avamine ebaõnnestus: {str(e)}")


def main():
    """Rakenduse käivituspunkt"""
    root = tk.Tk()
    app = FotodPdfiksGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main() 