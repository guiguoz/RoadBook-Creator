from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, KeepInFrame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io
import os
import math
import logging
from datetime import datetime
from typing import List, Optional, Tuple
from vignette_model import Vignette

# Import optionnel de svglib pour une conversion vectorielle
try:
    from svglib.svglib import svg2rlg
    SVGLIB_AVAILABLE = True
except ImportError:
    SVGLIB_AVAILABLE = False

class PDFExportError(Exception):
    """Custom exception for PDF export errors"""
    pass

class PDFExporter:
    def __init__(self, vignettes: List[Vignette]):
        self.vignettes = vignettes
        self.page_width, self.page_height = A4
        self.margin = 1.5 * cm

    def export(self, filename: Optional[str] = None) -> str:
        try:
            # Secure path construction to prevent path traversal
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            output_dir = os.path.join(base_dir, 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = f"roadbook_{timestamp}.pdf"
            else:
                # Sanitize user-provided filename to prevent path traversal
                safe_filename = os.path.basename(filename)
                if not safe_filename.endswith('.pdf'):
                    safe_filename += '.pdf'
            
            filename = os.path.join(output_dir, safe_filename)

            # Document
            doc = SimpleDocTemplate(
                filename,
                pagesize=A4,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )

            # Zone utile
            content_width = doc.width
            content_height = doc.height

            # Styles
            styles = getSampleStyleSheet()
            style_header = ParagraphStyle(
                name='HeaderSmall', parent=styles['Normal'], fontSize=8, leading=9, spaceAfter=2
            )
            style_obs = ParagraphStyle(
                name='ObsSmall', parent=styles['Normal'], fontSize=8, leading=9
            )

            # Calcul des distances cumulées
            cumul_dists = []
            cumul = 0
            for v in self.vignettes:
                cumul += v.inter_dist
                cumul_dists.append(int(cumul))

            n = len(self.vignettes)

            # Déterminer le nombre de colonnes (1 ou 2) et la hauteur des lignes
            # Hauteur minimale raisonnable par vignette (pour lisibilité)
            min_row_h = 2.8 * cm

            if n <= 1:
                columns = 1
                rows_per_col = max(1, n)
            else:
                # Essai en 1 colonne - Add validation to prevent division by zero
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

            # Construire la Table principale (rows_per_col x columns)
            main_rows = []

            # Préparer les index par colonne (remplissage vertical, puis on passe à la colonne suivante)
            # Col 0: indices 0..rows_per_col-1, Col 1: indices rows_per_col..2*rows_per_col-1, etc.
            for r in range(rows_per_col):
                row_cells = []
                for c in range(columns):
                    idx = c * rows_per_col + r
                    if idx < n:
                        v = self.vignettes[idx]
                        cumul_val = cumul_dists[idx]
                        cell = self._build_vignette_cell(
                            v,
                            cumul_val,
                            col_w,
                            row_h,
                            style_header,
                            style_obs
                        )
                        row_cells.append(cell)
                    else:
                        row_cells.append("")
                main_rows.append(row_cells)

            # Table principale
            main_table = Table(
                main_rows,
                colWidths=[col_w] * columns,
                rowHeights=[row_h] * rows_per_col
            )

            # Style de la table principale
            main_style_cmds = [
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]
            main_table.setStyle(TableStyle(main_style_cmds))

            # Forcer le contenu à tenir sur une seule page A4 en le réduisant si nécessaire
            kif = KeepInFrame(content_width, content_height, [main_table], mode='shrink')
            elements = [kif]
            doc.build(elements)
            return filename

        except (OSError, IOError) as e:
            logging.error(f"File system error during PDF creation: {e}")
            raise PDFExportError(f"Erreur d'accès fichier lors de la création du PDF : {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error during PDF creation: {e}")
            raise PDFExportError(f"Erreur lors de la création du PDF : {str(e)}")

    def _build_vignette_cell(
        self,
        v: Vignette,
        cumul_val: int,
        cell_w: float,
        cell_h: float,
        style_header: ParagraphStyle,
        style_obs: ParagraphStyle
    ):
        """Construit une ligne à 3 colonnes:
        - Col gauche (nuances de gris): 3 lignes (N°, Int, Tot)
        - Col milieu: schéma
        - Col droite: observations
        Le tout s'adapte en taille pour tenir en A4.
        """
        # Marges internes
        inner_pad = 2
        usable_w = max(1, cell_w - 2 * inner_pad)
        usable_h = max(1, cell_h - 2 * inner_pad)

        # Tailles de police "responsive"
        def clamp(x, lo, hi):
            return max(lo, min(hi, x))
        num_fs = int(clamp(usable_h * 0.26 / cm * 10, 7, 18))  # proportion de la hauteur
        lab_fs = int(clamp(usable_h * 0.18 / cm * 10, 6, 12))
        obs_fs = int(clamp(usable_h * 0.18 / cm * 10, 6, 12))

        style_num = ParagraphStyle(name='NumBox', parent=style_header, fontSize=num_fs, leading=num_fs+1, alignment=1)
        style_lab = ParagraphStyle(name='LabSmall', parent=style_header, fontSize=lab_fs, leading=lab_fs+1, alignment=1)
        style_obs_dyn = ParagraphStyle(name='ObsDyn', parent=style_obs, fontSize=obs_fs, leading=obs_fs+1)

        # Largeurs des colonnes: gauche ~18%, schéma ~60%, obs ~22%
        left_w = clamp(usable_w * 0.18, 1.2*cm, usable_w * 0.25)
        rem_w = usable_w - left_w
        obs_w = clamp(rem_w * 0.22, 2.0*cm, rem_w * 0.30)
        diagram_w = max(1, rem_w - obs_w)

        # Colonne gauche: 3 lignes avec nuances de gris
        # Palette bicolonne alternée selon le numéro pour faciliter la lecture
        base_sets = [
            (0.82, 0.88, 0.94),  # un peu plus sombre -> plus clair
            (0.86, 0.92, 0.97),  # un peu plus clair -> très clair
        ]
        b = base_sets[(int(v.num) - 1) % 2]
        g1, g2, g3 = (colors.Color(b[0], b[0], b[0]), colors.Color(b[1], b[1], b[1]), colors.Color(b[2], b[2], b[2]))

        num_para = Paragraph(f"<b>{int(v.num)}</b>", style_num)
        int_para = Paragraph(f"Distance int.: {int(v.inter_dist)} m", style_lab)
        tot_para = Paragraph(f"Distance totale: {int(cumul_val)} m", style_lab)

        left_tbl = Table(
            [[num_para], [int_para], [tot_para]],
            colWidths=[left_w],
            rowHeights=[usable_h*0.40, usable_h*0.30, usable_h*0.30]
        )
        left_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), g1),
            ('BACKGROUND', (0, 1), (0, 1), g2),
            ('BACKGROUND', (0, 2), (0, 2), g3),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.black),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))

        # Colonne milieu: schéma occupant toute la case avec padding minimal
        diagram_padding = 1  # Padding ultra minimal
        available_diagram_w = max(1, diagram_w - 2 * diagram_padding)
        available_diagram_h = max(1, usable_h - 2 * diagram_padding)
        diag_flow = self._process_diagram(v.diagram, available_diagram_w, available_diagram_h) if v.diagram else ""

        # Colonne droite: Observations (avec titre)
        obs_text = v.observations or ""
        max_chars = 200
        if len(obs_text) > max_chars:
            obs_text = obs_text[:max_chars - 3] + "..."
        obs_title_para = Paragraph("<b>Observations</b>", style_lab)
        obs_para = Paragraph(obs_text, style_obs_dyn)
        # Hauteur du titre d'observation
        obs_hdr_h = min(0.4 * cm, usable_h * 0.15)
        obs_tbl = Table(
            [[obs_title_para], [obs_para]],
            colWidths=[obs_w],
            rowHeights=[obs_hdr_h, max(1, usable_h - obs_hdr_h)]
        )
        obs_tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 1),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))

        # Vignette row (1 ligne, 3 colonnes)
        row_tbl = Table(
            [[left_tbl, diag_flow, obs_tbl]],
            colWidths=[left_w, diagram_w, obs_w],
            rowHeights=[usable_h]
        )
        row_tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),  # centre schéma
            ('LINEBEFORE', (2, 0), (2, 0), 0.75, colors.black),  # trait de séparation schéma/observations
            ('LEFTPADDING', (0, 0), (0, 0), 2),  # colonne gauche
            ('RIGHTPADDING', (0, 0), (0, 0), 2),
            ('TOPPADDING', (0, 0), (0, 0), 2),
            ('BOTTOMPADDING', (0, 0), (0, 0), 2),
            ('LEFTPADDING', (1, 0), (1, 0), 1),   # schéma avec padding ultra minimal
            ('RIGHTPADDING', (1, 0), (1, 0), 1),
            ('TOPPADDING', (1, 0), (1, 0), 1),
            ('BOTTOMPADDING', (1, 0), (1, 0), 1),
            ('LEFTPADDING', (2, 0), (2, 0), 2),   # observations
            ('RIGHTPADDING', (2, 0), (2, 0), 2),
            ('TOPPADDING', (2, 0), (2, 0), 2),
            ('BOTTOMPADDING', (2, 0), (2, 0), 2),
        ]))

        return row_tbl

    def _process_diagram(self, svg_data: str, max_width: float, max_height: float):
        """Convert SVG to maximum size Flowable that fits in available space"""
        if not svg_data:
            return ""

        # 1) Vectorial conversion via svglib
        if SVGLIB_AVAILABLE:
            try:
                svg_bytes = io.BytesIO(svg_data.encode('utf-8'))
                drawing = svg2rlg(svg_bytes)
                if drawing:
                    width = getattr(drawing, 'width', 0) or 0
                    height = getattr(drawing, 'height', 0) or 0
                    if width <= 0 or height <= 0:
                        try:
                            x1, y1, x2, y2 = drawing.getBounds()
                            width = max(1.0, (x2 - x1))
                            height = max(1.0, (y2 - y1))
                            try:
                                drawing.translate(-x1, -y1)
                            except AttributeError:
                                logging.debug("Drawing translate not available")
                        except (AttributeError, ValueError) as e:
                            logging.debug(f"Could not get drawing bounds: {e}")
                            width = 1.0
                            height = 1.0
                    
                    # Scale to maintain aspect ratio while maximizing size
                    sx = max_width / width
                    sy = max_height / height
                    s = min(sx, sy)  # Use smaller scale to maintain aspect ratio
                    
                    try:
                        drawing.scale(s, s)
                        drawing.width = width * s
                        drawing.height = height * s
                    except AttributeError:
                        logging.debug("Drawing scale not available")
                    return drawing
            except (ImportError, ValueError, AttributeError) as e:
                logging.debug(f"SVG vectorial conversion failed: {e}")

        # 2) Fallback: rasterize via Qt with cropping to content
        try:
            from PyQt5.QtSvg import QSvgRenderer
            from PyQt5.QtGui import QImage, QPainter
            from PyQt5.QtCore import QBuffer, QIODevice, QRectF

            renderer = QSvgRenderer(svg_data.encode('utf-8'))
            if not renderer.isValid():
                return ""

            # Render at high resolution to detect content bounds
            temp_size = 1000
            temp_image = QImage(temp_size, temp_size, QImage.Format_ARGB32)
            temp_image.fill(0xFFFFFFFF)
            temp_painter = QPainter(temp_image)
            renderer.render(temp_painter, QRectF(0, 0, temp_size, temp_size))
            temp_painter.end()
            
            # Find content bounds by scanning for non-white pixels
            min_x, min_y = temp_size, temp_size
            max_x, max_y = 0, 0
            
            for y in range(temp_size):
                for x in range(temp_size):
                    pixel = temp_image.pixel(x, y)
                    if pixel != 0xFFFFFFFF:  # Not white
                        min_x = min(min_x, x)
                        min_y = min(min_y, y)
                        max_x = max(max_x, x)
                        max_y = max(max_y, y)
            
            if min_x >= max_x or min_y >= max_y:
                return ""
            
            # Minimal margin around content for maximum size
            margin = 2
            content_x = max(0, min_x - margin)
            content_y = max(0, min_y - margin)
            content_w = min(temp_size - content_x, max_x - min_x + 2 * margin)
            content_h = min(temp_size - content_y, max_y - min_y + 2 * margin)
            
            # Calculate optimal size maintaining aspect ratio
            content_ratio = content_w / content_h if content_h > 0 else 1
            available_ratio = max_width / max_height if max_height > 0 else 1
            
            if content_ratio > available_ratio:
                # Content is wider - fit to width
                target_w = max_width
                target_h = max_width / content_ratio
            else:
                # Content is taller - fit to height  
                target_h = max_height
                target_w = max_height * content_ratio
            
            # Render final image at target size
            scale_factor = 4.0
            px_w = max(1, int(target_w * scale_factor))
            px_h = max(1, int(target_h * scale_factor))
            
            final_image = QImage(px_w, px_h, QImage.Format_ARGB32)
            final_image.fill(0xFFFFFFFF)
            final_painter = QPainter(final_image)
            final_painter.setRenderHint(QPainter.Antialiasing)
            
            # Scale and translate to crop to content area
            scale_x = px_w / temp_size
            scale_y = px_h / temp_size
            final_painter.scale(scale_x, scale_y)
            final_painter.translate(-content_x, -content_y)
            
            renderer.render(final_painter, QRectF(0, 0, temp_size, temp_size))
            final_painter.end()
            
            buf = QBuffer()
            buf.open(QIODevice.WriteOnly)
            final_image.save(buf, b"PNG")
            png_bytes = bytes(buf.data())
            buf.close()
            
            return Image(io.BytesIO(png_bytes), width=target_w, height=target_h)
        except (ImportError, RuntimeError, OSError) as e:
            logging.debug(f"SVG rasterization failed: {e}")
            return ""