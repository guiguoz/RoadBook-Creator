import os
import logging
import math
from datetime import datetime
from typing import List
from vignette_model import Vignette
from pdf_exporter import PDFExporter

class JPEGExporter:
    def __init__(self, vignettes: List[Vignette]):
        self.vignettes = vignettes

    def export(self, filename: str = None) -> str:
        try:
            # Secure path construction
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            output_dir = os.path.join(base_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = f"roadbook_{timestamp}.jpg"
            else:
                safe_filename = os.path.basename(filename)
                if not safe_filename.lower().endswith(('.jpg', '.jpeg')):
                    safe_filename += '.jpg'
            
            jpeg_path = os.path.join(output_dir, safe_filename)
            
            # Générer d'abord un PDF temporaire
            pdf_exporter = PDFExporter(self.vignettes)
            temp_pdf = pdf_exporter.export()
            
            # Convertir le PDF en JPEG
            self._convert_pdf_to_jpeg(temp_pdf, jpeg_path)
            
            # Nettoyer le PDF temporaire
            try:
                os.remove(temp_pdf)
            except:
                pass
            
            return jpeg_path
                
        except Exception as e:
            logging.error(f"JPEG export error: {e}", exc_info=True)
            raise

    def _convert_pdf_to_jpeg(self, pdf_path: str, jpeg_path: str):
        """Convertit un PDF en JPEG haute qualité"""
        try:
            # Méthode 1: Utiliser pdf2image si disponible
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(pdf_path, dpi=300, first_page=1, last_page=1)
                if images:
                    images[0].save(jpeg_path, 'JPEG', quality=95)
                    return
            except ImportError:
                pass
            
            # Méthode 2: Utiliser PyMuPDF si disponible
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(pdf_path)
                page = doc[0]
                mat = fitz.Matrix(4.17, 4.17)  # 300 DPI
                pix = page.get_pixmap(matrix=mat)
                pix.save(jpeg_path)
                doc.close()
                return
            except ImportError:
                pass
            
            # Méthode 3: Utiliser Pillow avec PyQt5 (fallback)
            self._convert_with_qt(pdf_path, jpeg_path)
            
        except Exception as e:
            logging.error(f"PDF to JPEG conversion failed: {e}")
            raise Exception(f"Impossible de convertir le PDF en JPEG: {e}")

    def _convert_with_qt(self, pdf_path: str, jpeg_path: str):
        """Conversion fallback - recréer directement l'image"""
        try:
            from PyQt5.QtGui import QPixmap, QPainter, QImage, QFont, QPen, QColor
            from PyQt5.QtCore import Qt, QRect
            from PyQt5.QtWidgets import QApplication
            
            # Créer une application Qt si nécessaire
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Créer une image A4 à 300 DPI
            width, height = 2480, 3508
            margin = 118
            
            image = QImage(width, height, QImage.Format_RGB32)
            image.fill(Qt.white)
            
            painter = QPainter(image)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            
            # Recréer le contenu identique au PDF
            self._draw_roadbook_content(painter, width, height, margin)
            
            painter.end()
            
            # Sauvegarder en JPEG
            image.save(jpeg_path, "JPEG", 95)
            
        except Exception as e:
            raise Exception(f"Conversion Qt échouée: {e}")
    
    def _draw_roadbook_content(self, painter, width, height, margin):
        """Dessine le contenu du roadbook identique au PDF"""
        from PyQt5.QtCore import QRect
        
        content_width = width - 2 * margin
        content_height = height - 2 * margin
        
        n = len(self.vignettes)
        min_row_h = int(content_height * 0.15)
        
        if n <= 1:
            columns = 1
            rows_per_col = max(1, n)
        else:
            if n > 0:
                row_h_one_col = content_height / n
                if row_h_one_col >= min_row_h:
                    columns = 1
                    rows_per_col = n
                else:
                    columns = 2
                    rows_per_col = math.ceil(n / 2)
            else:
                columns = 1
                rows_per_col = 1
        
        row_h = content_height / max(1, rows_per_col)
        col_w = content_width / columns
        
        # Calculer distances cumulées
        cumul_dists = []
        cumul = 0
        for v in self.vignettes:
            cumul += v.inter_dist
            cumul_dists.append(int(cumul))
        
        # Dessiner chaque vignette
        for i, vignette in enumerate(self.vignettes):
            col = i // rows_per_col
            row = i % rows_per_col
            
            x = margin + col * col_w
            y = margin + row * row_h
            
            self._draw_vignette_qt(painter, vignette, cumul_dists[i], 
                                 QRect(int(x), int(y), int(col_w), int(row_h)))
    
    def _draw_vignette_qt(self, painter, vignette, cumul_dist, rect):
        """Dessine une vignette avec PyQt5"""
        from PyQt5.QtCore import QRect
        from PyQt5.QtGui import QPen
        from PyQt5.QtCore import Qt
        
        # Bordure principale
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(rect)
        
        # Calculs identiques au PDF
        inner_pad = 6
        usable_w = max(1, rect.width() - 2 * inner_pad)
        usable_h = max(1, rect.height() - 2 * inner_pad)
        
        def clamp(x, lo, hi):
            return max(lo, min(hi, x))
        
        left_w = int(clamp(usable_w * 0.18, usable_w * 0.15, usable_w * 0.25))
        rem_w = usable_w - left_w
        obs_w = int(clamp(rem_w * 0.22, rem_w * 0.20, rem_w * 0.30))
        diagram_w = max(1, rem_w - obs_w)
        
        # Positions
        left_x = rect.x() + inner_pad
        diagram_x = left_x + left_w
        obs_x = diagram_x + diagram_w
        content_y = rect.y() + inner_pad
        
        # Colonne gauche
        self._draw_left_column_qt(painter, vignette, cumul_dist, 
                                QRect(left_x, content_y, left_w, usable_h))
        
        # Colonne schéma
        self._draw_diagram_qt(painter, vignette, 
                            QRect(diagram_x, content_y, diagram_w, usable_h))
        
        # Trait de séparation
        painter.setPen(QPen(Qt.black, 2))
        painter.drawLine(obs_x, content_y, obs_x, content_y + usable_h)
        
        # Colonne observations
        self._draw_observations_qt(painter, vignette, 
                                 QRect(obs_x, content_y, obs_w, usable_h))
    
    def _draw_left_column_qt(self, painter, vignette, cumul_dist, rect):
        """Dessine la colonne gauche avec PyQt5"""
        from PyQt5.QtCore import QRect, Qt
        from PyQt5.QtGui import QPen, QColor, QFont
        
        h1 = int(rect.height() * 0.40)
        h2 = int(rect.height() * 0.30)
        h3 = rect.height() - h1 - h2
        
        # Couleurs alternées
        base_sets = [(0.82, 0.88, 0.94), (0.86, 0.92, 0.97)]
        b = base_sets[(int(vignette.num) - 1) % 2]
        colors = [QColor(int(b[i] * 255), int(b[i] * 255), int(b[i] * 255)) for i in range(3)]
        
        # Section numéro
        num_rect = QRect(rect.x(), rect.y(), rect.width(), h1)
        painter.fillRect(num_rect, colors[0])
        painter.setPen(QPen(Qt.black, 2))
        painter.drawRect(num_rect)
        
        # Tailles de police responsive comme le PDF
        num_fs = max(12, int(rect.height() * 0.26 / 100 * 10))
        lab_fs = max(8, int(rect.height() * 0.18 / 100 * 10))
        
        font = QFont("Arial", num_fs, QFont.Bold)
        painter.setFont(font)
        painter.drawText(num_rect, Qt.AlignCenter, str(int(vignette.num)))
        
        # Section distance intermédiaire
        int_rect = QRect(rect.x(), rect.y() + h1, rect.width(), h2)
        painter.fillRect(int_rect, colors[1])
        painter.setPen(QPen(Qt.black, 1))
        painter.drawRect(int_rect)
        
        font = QFont("Arial", lab_fs)
        painter.setFont(font)
        painter.drawText(int_rect, Qt.AlignCenter, f"Distance int.: {int(vignette.inter_dist)} m")
        
        # Section distance totale
        tot_rect = QRect(rect.x(), rect.y() + h1 + h2, rect.width(), h3)
        painter.fillRect(tot_rect, colors[2])
        painter.drawRect(tot_rect)
        
        painter.drawText(tot_rect, Qt.AlignCenter, f"Distance totale: {cumul_dist} m")
    
    def _draw_observations_qt(self, painter, vignette, rect):
        """Dessine la colonne observations avec PyQt5"""
        from PyQt5.QtCore import QRect, Qt
        from PyQt5.QtGui import QPen, QFont
        
        obs_hdr_h = min(40, int(rect.height() * 0.15))
        
        # Taille de police responsive
        obs_fs = max(8, int(rect.height() * 0.18 / 100 * 10))
        
        # Titre
        title_rect = QRect(rect.x(), rect.y(), rect.width(), obs_hdr_h)
        font = QFont("Arial", max(8, obs_fs), QFont.Bold)
        painter.setFont(font)
        painter.setPen(QPen(Qt.black))
        painter.drawText(title_rect.adjusted(6, 3, -6, -3), Qt.AlignTop, "Observations")
        
        # Contenu
        if vignette.observations:
            content_rect = QRect(rect.x(), rect.y() + obs_hdr_h, 
                               rect.width(), max(1, rect.height() - obs_hdr_h))
            
            obs_text = vignette.observations
            if len(obs_text) > 200:
                obs_text = obs_text[:197] + "..."
            
            font = QFont("Arial", max(6, obs_fs - 2))
            painter.setFont(font)
            painter.drawText(content_rect.adjusted(6, 3, -6, -3), 
                           Qt.AlignTop | Qt.TextWordWrap, obs_text)
    
    def _draw_diagram_qt(self, painter, vignette, rect):
        """Dessine le schéma SVG avec PyQt5"""
        from PyQt5.QtSvg import QSvgRenderer
        from PyQt5.QtGui import QPixmap, QPainter as QtPainter
        from PyQt5.QtCore import Qt
        
        if vignette.diagram:
            try:
                # Marge élégante comme le PDF
                margin = 4
                available_w = max(1, rect.width() - 2 * margin)
                available_h = max(1, rect.height() - 2 * margin)
                
                renderer = QSvgRenderer(vignette.diagram.encode('utf-8'))
                if renderer.isValid():
                    # Obtenir les dimensions du SVG
                    svg_size = renderer.defaultSize()
                    if svg_size.width() > 0 and svg_size.height() > 0:
                        # Calculer l'échelle pour conserver les proportions
                        scale_x = available_w / svg_size.width()
                        scale_y = available_h / svg_size.height()
                        scale = min(scale_x, scale_y)
                        
                        # Taille finale
                        final_w = int(svg_size.width() * scale)
                        final_h = int(svg_size.height() * scale)
                        
                        # Créer le pixmap
                        pixmap = QPixmap(final_w, final_h)
                        pixmap.fill(Qt.white)
                        
                        svg_painter = QtPainter(pixmap)
                        svg_painter.setRenderHint(QtPainter.Antialiasing)
                        renderer.render(svg_painter)
                        svg_painter.end()
                        
                        # Centrer dans le rectangle
                        x = rect.x() + (rect.width() - final_w) // 2
                        y = rect.y() + (rect.height() - final_h) // 2
                        painter.drawPixmap(x, y, pixmap)
            except Exception as e:
                logging.error(f"Error rendering SVG in JPEG: {e}")