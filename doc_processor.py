import cv2
import numpy as np
from skimage.filters import threshold_local
import os
from PIL import Image, ImageEnhance
import pytesseract
import img2pdf
import importlib.util
import sys
import tempfile
import shutil
import re
import json
import csv
import warnings
from pdf2image import convert_from_path, convert_from_bytes

# Proovi laadida lzma_fix, mis asendab puuduva _lzma mooduli
try:
    import lzma_fix
except ImportError:
    pass

# Kontrolli, kas rembg on installitud
REMBG_AVAILABLE = importlib.util.find_spec("rembg") is not None
if REMBG_AVAILABLE:
    try:
        import rembg
        print("rembg teek on saadaval - AI-põhine tausta eemaldamine aktiveeritud")
    except ImportError as e:
        REMBG_AVAILABLE = False
        print(f"rembg teeki ei õnnestunud importida: {e}")
else:
    print("rembg teeki ei leitud - kasutatakse tavalist töötlust")

class DocumentProcessor:
    """Klass dokumendifotode töötlemiseks ja optimeerimiseks"""
    
    def __init__(self, debug=False, use_ai=True):
        """Initsialiseeri DocumentProcessor
        
        Args:
            debug (bool): Kui True, kuvatakse debug infot ja salvestatakse töötluse vaheetapid
            use_ai (bool): Kui True ja rembg on saadaval, kasutatakse AI-d tausta eemaldamiseks
        """
        self.debug = debug
        self.use_ai = use_ai and REMBG_AVAILABLE
        if self.use_ai:
            print("AI-põhine tausta eemaldamine lubatud")
        else:
            print("Kasutatakse klassikalist pilditöötlust tausta eemaldamiseks")
    
    def _resize_image(self, image, width=2000):
        """Muuda pildi suurust, säilitades pildisuhte
        
        Args:
            image: OpenCV pilt
            width: Sihtlaius
            
        Returns:
            Muudetud suurusega pilt
        """
        h, w = image.shape[:2]
        ratio = width / float(w)
        dim = (width, int(h * ratio))
        resized = cv2.resize(image, dim, interpolation=cv2.INTER_CUBIC)
        
        return resized
    
    def _remove_background_with_ai(self, image):
        """Eemalda pildilt taust kasutades rembg (AI-põhine)
        
        Args:
            image: OpenCV pilt (BGR formaat)
            
        Returns:
            Pilt ilma taustata (läbipaistev)
        """
        if not REMBG_AVAILABLE:
            return image
            
        try:
            # Konverdi PIL formaati
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            
            # Eemalda taust
            output = rembg.remove(pil_image)
            
            # Konverdi tagasi OpenCV formaati
            # Säilitame alpha kanali, mis tähistab läbipaistvust
            result = cv2.cvtColor(np.array(output), cv2.COLOR_RGBA2BGRA)
            
            return result
        except Exception as e:
            print(f"Viga AI-põhisel tausta eemaldamisel: {e}")
            # Kui AI töötlus ebaõnnestub, tagastame originaalpildi
            return image
    
    def _add_white_background_to_transparent(self, image):
        """Lisa valge taust läbipaistvale pildile
        
        Args:
            image: OpenCV pilt alpha kanaliga (BGRA)
            
        Returns:
            Pilt valge taustaga (BGR)
        """
        try:
            # Kontrolli, kas pildil on alpha kanal
            if image.shape[2] == 4:
                # Loo valge taust
                h, w = image.shape[:2]
                white_background = np.ones((h, w, 3), dtype=np.uint8) * 255
                
                # Eraldame alpha kanali
                alpha = image[:, :, 3] / 255.0
                
                # Laiendame alpha kanalit 3 kanaliks (BGR jaoks)
                alpha = np.repeat(alpha[:, :, np.newaxis], 3, axis=2)
                
                # Kombineerime pildi ja tausta
                foreground = image[:, :, 0:3].astype(float)
                background = white_background.astype(float)
                
                # Alpha blending
                result = cv2.convertScaleAbs(foreground * alpha + background * (1 - alpha))
                
                return result
            else:
                # Kui alpha kanalit pole, tagastame originaalpildi
                return image
        except Exception as e:
            print(f"Viga läbipaistva tausta töötlemisel: {e}")
            # Kui töötlus ebaõnnestub, tagastame originaalpildi 3 kanaliga
            if image.shape[2] == 4:
                return image[:, :, 0:3]
            return image
    
    def _find_document_contour(self, image):
        """Leia dokumendi kontuur pildil - täiustatud versioon
        
        Args:
            image: OpenCV pilt
            
        Returns:
            Dokumendi kontuur või None, kui kontuuri ei leitud
        """
        # Konverdi hallskaalasse ja paranda kontrasti
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Rakenda mitut erinevat eeltöötlust tulemuste parandamiseks
        # 1. Meetod - Adaptiivne lävistamine kontrasti suurendamiseks
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                      cv2.THRESH_BINARY, 11, 2)
        
        # 2. Meetod - Canny servatuvastus
        edges = cv2.Canny(blurred, 50, 150)
        
        # Kombineeri meetodid parema tulemuse saamiseks
        combined = cv2.bitwise_or(thresh, edges)
        
        # Sulge väikesed augud kontuuri parandamiseks
        kernel = np.ones((5,5), np.uint8)
        dilated = cv2.dilate(combined, kernel, iterations=1)
        closed = cv2.erode(dilated, kernel, iterations=1)
        
        # Leia kontuurid
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Sorteeri kontuurid suuruse järgi kahanevalt
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        
        # Otsi dokumendi kontuuri
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            
            # Dokumendi kontuur võib olla 4-nurkne (nelinurk) või muu kuju (5-8 nurka)
            if 4 <= len(approx) <= 8:
                # Kontrolli, et kontuur oleks piisavalt suur (vähemalt 20% kogu pildist)
                # Vähendame miinimumala, et tuvastada rohkem dokumente
                area = cv2.contourArea(contour)
                img_area = image.shape[0] * image.shape[1]
                if area > 0.2 * img_area:
                    # Kui kontuuri punktide arv pole 4, teisendame selle nelinurgaks
                    if len(approx) != 4:
                        # Leia kontuuri ümbritsev nelinurk
                        rect = cv2.minAreaRect(contour)
                        box = cv2.boxPoints(rect)
                        approx = np.int0(box)
                    
                    return approx
        
        # Kui dokumendi kontuuri ei leitud, proovime alternatiivset meetodit
        return self._find_document_alternative(image)
    
    def _find_document_alternative(self, image):
        """Alternatiivne meetod dokumendi kontuuri leidmiseks, kui tavaline meetod ebaõnnestub
        
        Args:
            image: OpenCV pilt
            
        Returns:
            Dokumendi kontuur või None, kui kontuuri ei leitud
        """
        # Proovime taustavärvi eemaldamist
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Leiame taustavärvi (eeldame, et see on pildi nurkades)
        h, w = gray.shape
        corner_pixels = [
            gray[0, 0],
            gray[0, w-1],
            gray[h-1, 0],
            gray[h-1, w-1]
        ]
        avg_bg = np.mean(corner_pixels)
        
        # Loome maski taustavärvi eemaldamiseks
        mask = cv2.threshold(gray, avg_bg * 0.9, 255, cv2.THRESH_BINARY)[1]
        
        # Eraldame dokumendi
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Võtame suurima kontuuri
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Kontrolli, et kontuur oleks piisavalt suur (vähemalt 10% kogu pildist)
            area = cv2.contourArea(largest_contour)
            img_area = image.shape[0] * image.shape[1]
            
            if area > 0.1 * img_area:
                # Leia kontuuri ümbritsev nelinurk
                rect = cv2.minAreaRect(largest_contour)
                box = cv2.boxPoints(rect)
                return np.int0(box)
        
        # Kui kõik meetodid ebaõnnestuvad, loome vaikimisi nelinurga, mis katab pildi siseosa
        # Jätame välja 10% äärtelt, eeldades, et see võib olla taust
        h, w = image.shape[:2]
        margin_x = int(w * 0.05)  # 5% margin vasakult ja paremalt
        margin_y = int(h * 0.05)  # 5% margin ülevalt ja alt
        
        box = np.array([
            [margin_x, margin_y],
            [w - margin_x, margin_y],
            [w - margin_x, h - margin_y],
            [margin_x, h - margin_y]
        ])
        
        return box
    
    def _order_points(self, pts):
        """Järjesta punktid [ülemine-vasak, ülemine-parem, alumine-parem, alumine-vasak]
        
        Args:
            pts: Punktide massiiv
            
        Returns:
            Järjestatud punktide massiiv
        """
        rect = np.zeros((4, 2), dtype="float32")
        
        # Ülemine-vasak punkt on väikseim x+y summa
        # Alumine-parem punkt on suurim x+y summa
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Ülemine-parem punkt on väikseim y-x vahe
        # Alumine-vasak punkt on suurim y-x vahe
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        
        return rect
    
    def _apply_perspective_transform(self, image, pts):
        """Rakenda perspektiivi transform, et dokument sirgestada
        
        Args:
            image: OpenCV pilt
            pts: Dokumendi nelja nurga koordinaadid
            
        Returns:
            Perspektiivi transformiga pilt
        """
        rect = self._order_points(pts.reshape(4, 2))
        (tl, tr, br, bl) = rect
        
        # Arvuta uue dokumendi laius
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        
        # Arvuta uue dokumendi kõrgus
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        
        # Sihtpunktid peale perspektiivi transformi
        dst = np.array([
            [0, 0],  # ülemine-vasak
            [maxWidth - 1, 0],  # ülemine-parem
            [maxWidth - 1, maxHeight - 1],  # alumine-parem
            [0, maxHeight - 1]  # alumine-vasak
        ], dtype="float32")
        
        # Arvuta perspektiivi transform maatriks ja rakenda see
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        
        return warped
    
    def _enhance_document_for_kvitungs(self, image):
        """Paranda dokumendi kvaliteeti spetsiaalselt kviitungitele
        
        Args:
            image: OpenCV pilt
            
        Returns:
            Parandatud kvaliteediga pilt
        """
        # Konverdi hallskaalasse - see on parem kviitungite jaoks
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Esimene meetod: adaptiivse läve rakendamine, hästi soome mustale tekstile valgel taustal
        try:
            # Suurendame pildi kontrasti
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
            
            # Adaptiivne läveväärtus paremate tulemuste jaoks
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 21, 11
            )
            
            return binary
            
        except Exception as e:
            print(f"Viga kviitungi töötlemisel: {e}")
            return gray
    
    def _enhance_document(self, image):
        """Paranda dokumendi kvaliteeti
        
        Args:
            image: OpenCV pilt
            
        Returns:
            Parandatud kvaliteediga pilt
        """
        # Konverdi värviruumi ja eemaldame müra
        # Kasutame värviruumi säilitavat meetodit parema kvaliteedi saamiseks
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        
        # Konverdi PIL formaati täiendavate paranduste jaoks
        pil_image = Image.fromarray(cv2.cvtColor(denoised, cv2.COLOR_BGR2RGB))
        
        # Suurendame teravust
        sharpener = ImageEnhance.Sharpness(pil_image)
        sharpened = sharpener.enhance(2.0)  # Suurendame teravust 2x
        
        # Suurendame kontrasti
        enhancer = ImageEnhance.Contrast(sharpened)
        enhanced = enhancer.enhance(1.8)  # Suurendame kontrasti 1.8x
        
        # Parandame heledust
        brightness = ImageEnhance.Brightness(enhanced)
        brightened = brightness.enhance(1.1)  # Väike heleduse tõstmine
        
        # Tagasta parandatud pilt OpenCV formaadis
        result = cv2.cvtColor(np.array(brightened), cv2.COLOR_RGB2BGR)
        
        return result
    
    def _optimize_image_for_pdf(self, image, optimization_level=2):
        """Optimeeri pilti PDF-i suuruse vähendamiseks
        
        Args:
            image: OpenCV pilt
            optimization_level: Optimeerimise tase (0-3)
            
        Returns:
            Optimeeritud pilt
        """
        # Optimeerimise tasemed:
        # 0 - Minimaalne optimeerimine
        # 1 - Kerge optimeerimine
        # 2 - Keskmine optimeerimine (vaikimisi)
        # 3 - Tugev optimeerimine
        
        # Kontrolli, kas pilt on juba must-valge (1 kanal)
        if len(image.shape) == 2 or image.shape[2] == 1:
            # Must-valge piltide puhul ära rohkem konverteeri
            optimized = image
        else:
            # Värviliste piltide puhul konverteeri hallskaalasse, kui optimeerimistase > 1
            if optimization_level >= 2:
                optimized = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                optimized = image
                
        # Suuruse skaleerimine vastavalt optimeerimistasemele
        scale_factor = 1.0
        if optimization_level == 1:
            scale_factor = 0.8  # 80% originaalsuurusest
        elif optimization_level == 2:
            scale_factor = 0.6  # 60% originaalsuurusest
        elif optimization_level == 3:
            scale_factor = 0.4  # 40% originaalsuurusest
            
        if scale_factor < 1.0:
            h, w = optimized.shape[:2]
            new_size = (int(w * scale_factor), int(h * scale_factor))
            optimized = cv2.resize(optimized, new_size, interpolation=cv2.INTER_AREA)
        
        return optimized
    
    def _add_white_background(self, image):
        """Lisa pildile valge taust PDF-i jaoks
        
        Args:
            image: OpenCV pilt
            
        Returns:
            Valge taustaga pilt
        """
        # Kontrolli, kas pildil on alpha kanal (BGRA)
        if len(image.shape) == 3 and image.shape[2] == 4:
            return self._add_white_background_to_transparent(image)
        
        # Tavapärane valge tausta lisamine BGR piltidele
        if len(image.shape) == 2:  # Must-valge pilt
            h, w = image.shape
            background = np.ones((h, w), dtype=np.uint8) * 255
        else:  # Värviline pilt
            h, w, c = image.shape
            background = np.ones((h, w, c), dtype=np.uint8) * 255
            
        # Kopeeri pilt valge tausta peale
        result = background.copy()
        if len(image.shape) == 2:  # Must-valge pilt
            result = image
        else:  # Värviline pilt
            np.copyto(result, image)
            
        return result
    
    def _is_kvitung(self, image_path):
        """Kontrolli kas pilt on tõenäoliselt kviitung
        
        Args:
            image_path: Pildi tee
            
        Returns:
            Boolean: Tõene kui tõenäoliselt on kviitung
        """
        # Kasutame faili nime ja/või pildi omadusi, et hinnata tõenäosust
        filename = os.path.basename(image_path).lower()
        if "kvit" in filename or "arve" in filename or "tsek" in filename or "tšek" in filename:
            return True
            
        # Kasutame pildi mõõtmeid ja aspekti suhet
        image = cv2.imread(image_path)
        if image is None:
            return False
            
        h, w = image.shape[:2]
        aspect_ratio = h / w
        
        # Kviitungid on tavaliselt pikad ja kitsad (kõrge/lai suhe)
        if aspect_ratio > 1.5:  # Kõrgem kui laiem
            return True
            
        # Vaatame ka pildi heledust - kviitungid on tavaliselt valge taustaga
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        avg_brightness = np.mean(gray)
        if avg_brightness > 180:  # Väga hele pilt
            return True
            
        return False
    
    def process_image(self, image_path, output_dir=None, optimization_level=2):
        """Töötle dokumendifotot
        
        Args:
            image_path: Töödeldava pildi tee
            output_dir: Väljundkaust debugimiseks
            optimization_level: Optimeerimise tase
            
        Returns:
            Töödeldud pilt
        """
        # Loe pilt
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Ei suutnud pilti lugeda: {image_path}")
        
        # Kontrolli, kas see on kviitung
        is_kvitung = self._is_kvitung(image_path)
        
        # AI-põhine töötlus, kui see on lubatud
        if self.use_ai:
            print(f"Kasutan AI-d dokumendi tausta eemaldamiseks: {image_path}")
            # Tee pilt AI töötluseks sobivaks suuruseks
            resized_for_ai = self._resize_image(image, width=1500)
            # Eemalda taust AI abiga
            result_with_transparency = self._remove_background_with_ai(resized_for_ai)
            # Lisa valge taust
            result = self._add_white_background_to_transparent(result_with_transparency)
            
            # Dokumendi kvaliteedi parandamine vastavalt dokumendi tüübile
            if is_kvitung and len(result.shape) == 3:  # Veendu, et värviline kviitung
                result = self._enhance_document_for_kvitungs(result)
            elif optimization_level < 2:  # Kui ei muuda halliks, siis paranda kvaliteeti
                result = self._enhance_document(result)
            
            # Salvesta debug pildid, kui vajalik
            if self.debug and output_dir:
                os.makedirs(output_dir, exist_ok=True)
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                cv2.imwrite(os.path.join(output_dir, f"{base_name}_1_original.jpg"), image)
                
                # Salvesta AI tulemus, kui see on saadaval
                if result_with_transparency is not None:
                    # Salvesta BGRA pilt PNG formaadis, et säilitada läbipaistvus
                    cv2.imwrite(os.path.join(output_dir, f"{base_name}_2_ai_bg_removed.png"), result_with_transparency)
                
                cv2.imwrite(os.path.join(output_dir, f"{base_name}_3_enhanced.jpg"), result)
        
        else:
            # Klassikaline töötlus ilma AI-ta
            # Muuda pildi suurust töötlemiseks
            orig = image.copy()
            image = self._resize_image(image, width=2000)
            
            # Leia dokumendi kontuur
            contour = self._find_document_contour(image)
            
            # Protsessi kontuuriga leitud dokument, isegi kviitungite puhul
            if contour is not None:
                print(f"Info: Dokumendi kontuur leitud pildil {image_path}.")
                
                # Rakenda perspektiivi transform
                warped = self._apply_perspective_transform(orig, contour.astype(np.float32) * (orig.shape[1] / 2000.0))
                
                # Paranda dokumendi kvaliteeti vastavalt dokumendi tüübile
                if is_kvitung:
                    result = self._enhance_document_for_kvitungs(warped)
                else:
                    result = self._enhance_document(warped)
                    
                # Lisa valge taust, et PDF-is ei oleks läbipaistvust
                result = self._add_white_background(result)
            else:
                # Kui kontuuri ei leitud, kasuta kogu pilti
                print(f"Info: Dokumendi kontuuri ei leitud pildil {image_path}.")
                
                # Kviitungite puhul kasutame spetsiaalset töötlusmeetodit, muidu tavalist
                if is_kvitung:
                    # Teeme pildi suuremaks
                    resized = self._resize_image(orig, width=2000)
                    result = self._enhance_document_for_kvitungs(resized)
                else:
                    result = self._enhance_document(orig)
                
                # Lisa valge taust, et PDF-is ei oleks läbipaistvust
                result = self._add_white_background(result)
                
            # Salvesta vaheetapid, kui debug on lubatud
            if self.debug and output_dir:
                os.makedirs(output_dir, exist_ok=True)
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                
                cv2.imwrite(os.path.join(output_dir, f"{base_name}_1_original.jpg"), orig)
                if contour is not None:
                    cv2.imwrite(os.path.join(output_dir, f"{base_name}_2_contour.jpg"), cv2.drawContours(image.copy(), [contour], -1, (0, 255, 0), 3))
                    cv2.imwrite(os.path.join(output_dir, f"{base_name}_3_warped.jpg"), warped)
                cv2.imwrite(os.path.join(output_dir, f"{base_name}_4_enhanced.jpg"), result)
        
        # Optimeerime pilti PDF-i suuruse vähendamiseks
        result = self._optimize_image_for_pdf(result, optimization_level)
        
        return result
    
    def convert_to_pdf(self, image_paths, output_path, dpi=300, optimization_level=2):
        """Konverdi pildid PDF-iks
        
        Args:
            image_paths: List pildifailide teedega
            output_path: PDF-faili väljundtee
            dpi: Pildi resolutsioon punktides tolli kohta
            optimization_level: Optimeerimise tase PDF suuruse vähendamiseks
        """
        processed_images = []
        
        for image_path in image_paths:
            # Töötle pilti
            processed = self.process_image(image_path, optimization_level=optimization_level)
            
            # Arvuta JPEG kvaliteet vastavalt optimeerimistasemele
            jpeg_quality = 100
            if optimization_level == 1:
                jpeg_quality = 90
            elif optimization_level == 2:
                jpeg_quality = 80
            elif optimization_level == 3:
                jpeg_quality = 65
            
            # Salvesta töödeldud pilt ajutiselt kohandatud kvaliteediga
            temp_path = f"temp_{os.path.basename(image_path)}"
            cv2.imwrite(temp_path, processed, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
            processed_images.append(temp_path)
        
        # Arvuta DPI vastavalt optimeerimistasemele
        output_dpi = int(dpi)
        if optimization_level >= 2:
            output_dpi = min(300, output_dpi)  # Piira DPI väärtust 300-ga
        if optimization_level >= 3:
            output_dpi = min(200, output_dpi)  # Piira DPI väärtust 200-ga
        
        # Konverdi töödeldud pildid PDF-iks
        with open(output_path, "wb") as f:
            # Kasuta optimeeritud DPI väärtust img2pdf puhul
            f.write(img2pdf.convert(processed_images, dpi=output_dpi))
        
        # Kustuta ajutised pildid
        for temp_path in processed_images:
            os.remove(temp_path)
    
    def ocr_document(self, image_path, lang="eng"):
        """Teksti tuvastamine pildilt
        
        Args:
            image_path: Pildi tee
            lang: OCR keele kood
            
        Returns:
            Tuvastatud tekst
        """
        # Töötle pilti ilma optimeerimiseta (OCR vajab head kvaliteeti)
        processed = self.process_image(image_path, optimization_level=0)
        
        # Salvesta töödeldud pilt ajutiselt OCR-i jaoks
        temp_path = f"temp_ocr_{os.path.basename(image_path)}"
        cv2.imwrite(temp_path, processed)
        
        # OCR seadistused
        config = '--psm 6'  # Eeldame, et tekst on ühel real
        
        # Tuvasta tekst
        text = pytesseract.image_to_string(Image.open(temp_path), lang=lang, config=config)
        
        # Kustuta ajutine pilt
        os.remove(temp_path)
        
        return text
    
    def extract_structured_data(self, image_path, lang="est"):
        """Eraldab struktureeritud andmeid dokumendist
        
        Args:
            image_path: Pildi tee
            lang: OCR keele kood
            
        Returns:
            Dict struktureeritud andmetega (arve number, kuupäev, summa jne)
        """
        # Töötle pilti OCR-i jaoks optimeeritud viisil
        processed = self.process_image(image_path, optimization_level=0)
        
        # Salvesta töödeldud pilt ajutiselt OCR-i jaoks
        temp_path = f"temp_ocr_{os.path.basename(image_path)}"
        cv2.imwrite(temp_path, processed)
        
        # Kasuta täiustatud OCR seadistusi
        config = '--psm 6 --oem 1'  # 1 = LSTM mootor, mis on täpsem
        
        # Kasuta Tesseract OCR-i, et eraldada tekst
        text = pytesseract.image_to_string(Image.open(temp_path), lang=lang, config=config)
        
        # Eraldame lisaks tekstiplokkide andmed koos koordinaatidega
        data = pytesseract.image_to_data(Image.open(temp_path), lang=lang, config=config, output_type=pytesseract.Output.DICT)
        
        # Kustuta ajutine pilt
        os.remove(temp_path)
        
        # Struktureeritud andmete eraldamine
        structured_data = self._parse_invoice_data(text, data)
        
        return structured_data
    
    def _parse_invoice_data(self, text, ocr_data):
        """Parsi arve tekst struktureeritud andmeteks
        
        Args:
            text: OCR-iga tuvastatud tekst
            ocr_data: Tesseracti väljund sõnastiku kujul
            
        Returns:
            Dict struktureeritud andmetega
        """
        # Põhistruktuur väljundandmete jaoks
        result = {
            "invoice_number": None,
            "invoice_date": None,
            "due_date": None,
            "total_amount": None,
            "tax_amount": None,
            "supplier_name": None,
            "supplier_reg_number": None,
            "line_items": []
        }
        
        # Regulaaravaldised erinevate andmeväljade tuvastamiseks
        # Arve number (otsime standardseid formaate)
        invoice_number_patterns = [
            r"(?:arve\s*nr|invoice\s*no|arve\s*number)[:\.\s]*([A-Z0-9\-\/]+)",
            r"(?:arve|invoice)[:\.\s]*([A-Z0-9\-\/]+)"
        ]
        
        # Kuupäevad
        date_patterns = [
            r"(?:kuupäev|date)[:\.\s]*(\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{2,4})",
            r"(\d{1,2}[\.\/\-]\d{1,2}[\.\/\-]\d{2,4})"
        ]
        
        # Summa
        amount_patterns = [
            r"(?:summa|kokku|total)[:\.\s]*(\d+[,\.]\d{2})",
            r"(?:summa|kokku|total)[:\.\s]*(\d+)[€\s]",
            r"€\s*(\d+[,\.]\d{2})"
        ]
        
        # Käibemaks
        tax_patterns = [
            r"(?:käibemaks|km|vat)[:\.\s]*(\d+[,\.]\d{2})",
            r"(?:käibemaks|km|vat)[:\.\s]*(\d+)[€\s]"
        ]
        
        # Tarnija nimi
        supplier_patterns = [
            r"(?:müüja|supplier|vendor)[:\.\s]*([^\n]+)"
        ]
        
        # Registreerimiskood / VAT number
        reg_number_patterns = [
            r"(?:reg\.\s*nr|registration\s*no|reg\s*code)[:\.\s]*([A-Z0-9]+)",
            r"(?:kmkr|vat\s*no)[:\.\s]*([A-Z0-9]+)"
        ]
        
        # Otsime iga välja regulaaravaldiste abil
        for pattern in invoice_number_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["invoice_number"] = match.group(1).strip()
                break
        
        # Kuupäevade otsing - arveldamise kuupäev on tavaliselt esimene
        date_matches = []
        for pattern in date_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                date_matches.append(match.group(1).strip())
        
        if len(date_matches) >= 1:
            result["invoice_date"] = date_matches[0]
        if len(date_matches) >= 2:
            result["due_date"] = date_matches[1]
        
        # Summa otsing
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Teisendame tekstilise summa numbriks
                amount_str = match.group(1).strip().replace(',', '.')
                try:
                    result["total_amount"] = float(amount_str)
                except ValueError:
                    pass
                break
        
        # Käibemaksu otsing
        for pattern in tax_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Teisendame tekstilise summa numbriks
                tax_str = match.group(1).strip().replace(',', '.')
                try:
                    result["tax_amount"] = float(tax_str)
                except ValueError:
                    pass
                break
        
        # Tarnija nime otsing
        for pattern in supplier_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["supplier_name"] = match.group(1).strip()
                break
        
        # Registreerimisnumbri otsing
        for pattern in reg_number_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["supplier_reg_number"] = match.group(1).strip()
                break
        
        # Kui tarnija nimi puudub, proovime määrata seda esimese tekstirea põhjal
        if not result["supplier_name"] and len(text.strip().split("\n")) > 0:
            result["supplier_name"] = text.strip().split("\n")[0].strip()
        
        # Proovime tuvastada ka tabelis olevaid ridu
        lines = text.split('\n')
        line_items = []
        
        # Otsime tabelit ridades (lihtsustatud, eeldab, et kogus, ühik, hind on reas)
        for line in lines:
            # Kui rida sisaldab numbrit, potentsiaalselt hinda ja mõnda ühikut
            if re.search(r'\d+[,\.]\d{2}', line) and re.search(r'\b(tk|pcs|kg|g|m|l)\b', line, re.IGNORECASE):
                # Eraldame rea osadeks
                parts = re.split(r'\s{2,}', line)
                if len(parts) >= 3:
                    item = {
                        "description": parts[0].strip(),
                        "quantity": None,
                        "unit_price": None,
                        "total": None
                    }
                    
                    # Proovime leida kogust
                    quantity_match = re.search(r'(\d+(?:[,\.]\d+)?)\s*(tk|pcs|kg|g|m|l)', line, re.IGNORECASE)
                    if quantity_match:
                        try:
                            item["quantity"] = float(quantity_match.group(1).replace(',', '.'))
                        except ValueError:
                            pass
                    
                    # Proovime leida hinda
                    price_match = re.search(r'(\d+[,\.]\d{2})', line)
                    if price_match:
                        try:
                            item["unit_price"] = float(price_match.group(1).replace(',', '.'))
                        except ValueError:
                            pass
                    
                    line_items.append(item)
        
        result["line_items"] = line_items
        
        return result
    
    def export_invoice_data_to_csv(self, structured_data, output_path):
        """Ekspordi struktureeritud andmed CSV failina Dolibarr'i jaoks
        
        Args:
            structured_data: Struktureeritud andmed (sõnastik)
            output_path: Väljundfaili tee
        """
        # CSV päised vastavalt Dolibarr'i impordi nõuetele
        # NB! Täpne formaat võib sõltuda Dolibarr'i versioonist ja seadistusest
        headers = [
            "invoice_ref", "invoice_date", "due_date", 
            "total_ttc", "total_vat", "supplier_name", "supplier_vat"
        ]
        
        # Koostame andmerea
        row = [
            structured_data["invoice_number"] or "",
            structured_data["invoice_date"] or "",
            structured_data["due_date"] or "",
            str(structured_data["total_amount"] or ""),
            str(structured_data["tax_amount"] or ""),
            structured_data["supplier_name"] or "",
            structured_data["supplier_reg_number"] or ""
        ]
        
        # Kirjutame CSV faili
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(headers)
            writer.writerow(row)
        
        # Kui on rea-elemendid, lisame ka need eraldi failina
        if structured_data["line_items"]:
            items_output_path = os.path.splitext(output_path)[0] + "_items.csv"
            item_headers = ["description", "quantity", "unit_price", "total"]
            
            with open(items_output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(item_headers)
                for item in structured_data["line_items"]:
                    writer.writerow([
                        item["description"] or "",
                        str(item["quantity"] or ""),
                        str(item["unit_price"] or ""),
                        str(item["total"] or "")
                    ])
    
    def export_invoice_data_to_json(self, structured_data, output_path):
        """Ekspordi struktureeritud andmed JSON failina
        
        Args:
            structured_data: Struktureeritud andmed (sõnastik)
            output_path: Väljundfaili tee
        """
        import json
        
        # Salvesta JSON formaadis
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, indent=2, ensure_ascii=False)
    
    def process_pdf(self, pdf_path, output_dir=None, dpi=300):
        """
        Töötleb PDF-faili ja konverteerib selle piltideks
        
        Args:
            pdf_path: PDF-faili tee
            output_dir: Väljundkataloog piltide salvestamiseks
            dpi: Pildi resolutsioon punktides tolli kohta
            
        Returns:
            List pildifailide teedega
        """
        # Kontrolli, kas väljundkataloog on määratud
        if output_dir is None:
            # Loo ajutine kataloog
            output_dir = tempfile.mkdtemp(prefix="pdf_images_")
        else:
            # Veendu, et väljundkataloog eksisteerib
            os.makedirs(output_dir, exist_ok=True)
        
        # Konverteeri PDF piltideks
        try:
            print(f"Konverteerin PDF-faili {pdf_path} piltideks...")
            images = convert_from_path(pdf_path, dpi=dpi)
            
            # Salvesta pildid
            image_paths = []
            for i, image in enumerate(images):
                # Loo failinimi
                image_name = f"page_{i+1:03d}.jpg"
                image_path = os.path.join(output_dir, image_name)
                
                # Salvesta pilt
                image.save(image_path, 'JPEG')
                image_paths.append(image_path)
                
            print(f"PDF konverteeritud: {len(image_paths)} lehekülge")
            return image_paths
            
        except Exception as e:
            print(f"Viga PDF konverteerimisel: {str(e)}")
            return []
            
    def extract_text_from_pdf(self, pdf_path, lang="est", dpi=300):
        """
        Eraldab PDF-failist teksti OCR abil
        
        Args:
            pdf_path: PDF-faili tee
            lang: OCR keele kood
            dpi: Pildi resolutsioon punktides tolli kohta
            
        Returns:
            str: Eraldatud tekst
        """
        # Konverteeri PDF piltideks
        temp_dir = tempfile.mkdtemp(prefix="pdf_ocr_")
        try:
            # Töötleme PDF ja saame pildifailid
            image_paths = self.process_pdf(pdf_path, output_dir=temp_dir, dpi=dpi)
            
            # Eralda tekst igalt pildilt
            full_text = ""
            for image_path in image_paths:
                # Tee OCR
                text = self.ocr_document(image_path, lang=lang)
                full_text += text + "\n\n"
            
            return full_text
            
        finally:
            # Puhasta ajutised failid
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    def extract_structured_data_from_pdf(self, pdf_path, lang="est", dpi=300):
        """
        Eraldab PDF-failist struktureeritud andmed
        
        Args:
            pdf_path: PDF-faili tee
            lang: OCR keele kood
            dpi: Pildi resolutsioon punktides tolli kohta
            
        Returns:
            dict: Struktureeritud andmed
        """
        # Konverteeri PDF piltideks
        temp_dir = tempfile.mkdtemp(prefix="pdf_data_")
        try:
            # Töötleme PDF ja saame pildifailid
            image_paths = self.process_pdf(pdf_path, output_dir=temp_dir, dpi=dpi)
            
            # Kogume kõigi lehtede andmed
            all_data = {}
            for i, image_path in enumerate(image_paths):
                # Eralda andmed igalt lehelt
                data = self.extract_structured_data(image_path, lang=lang)
                
                # Ühenda andmed
                if i == 0:  # Esimene lehekülg
                    all_data = data
                else:
                    # Lisa järgnevate lehtede andmed (kui on)
                    if 'items' in data and 'items' in all_data:
                        all_data['items'].extend(data.get('items', []))
                    # Täienda puuduvaid andmeid
                    for key, value in data.items():
                        if key != 'items' and not all_data.get(key):
                            all_data[key] = value
            
            return all_data
            
        finally:
            # Puhasta ajutised failid
            shutil.rmtree(temp_dir, ignore_errors=True) 