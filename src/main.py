#!/usr/bin/env python3
import sys
import os
import traceback
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
                           QHeaderView, QMessageBox, QSizePolicy, QDialog, QLabel)
from PyQt5.QtCore import Qt, QPointF, QByteArray, QRectF, QTimer
from PyQt5.QtGui import QPixmap, QImage, QPainter
from PyQt5.QtSvg import QSvgWidget, QSvgRenderer
from vignette_editor import VignetteEditor
from vignette_model import Vignette
from pdf_exporter import PDFExporter, PDFExportError
from widgets import DistanceTableItem

class RoadBookApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.vignettes = []
        self.current_filename = None
        self.has_unsaved_changes = False
        self.initUI()
        self._setupAutoSave()
        self._checkForUpdates()

    def initUI(self):
        self.setWindowTitle('📍 Éditeur de Road Book')
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QTableWidget {
                gridline-color: #ddd;
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #e0e0e0;
                padding: 8px;
                border: 1px solid #ccc;
                font-weight: bold;
            }
        """)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Connecter le signal de modification de cellule
        self.table_modified = False

        # Create toolbar with buttons
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        
        # Ajouter les boutons avec icônes
        btn_add = QPushButton('➕ Ajouter Vignette', self)
        btn_delete = QPushButton('🗑️ Supprimer vignette', self)

        btn_export = QPushButton('📄 Exporter PDF', self)
        btn_save = QPushButton('💾 Sauvegarder', self)
        btn_open = QPushButton('📂 Ouvrir', self)
        btn_infos = QPushButton('ℹ️ Infos', self)
        
        btn_export.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        

        
        btn_infos.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        
        btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)

        # Connect button signals
        btn_add.clicked.connect(self.addVignette)
        btn_delete.clicked.connect(self.deleteSelected)

        btn_export.clicked.connect(self.exportPDF)
        btn_save.clicked.connect(self.saveRoadbook)
        btn_open.clicked.connect(self.openRoadbook)
        btn_infos.clicked.connect(self.showInfos)

        # Add buttons to toolbar directly
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_delete)

        toolbar.addWidget(btn_export)
        toolbar.addWidget(btn_save)
        toolbar.addWidget(btn_open)
        toolbar.addWidget(btn_infos)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Create table with single column layout
        self.table = QTableWidget()
        self.table.setColumnCount(5)  # Une seule colonne de 5 champs
        self.table.setHorizontalHeaderLabels([
            '📍 #', '📏 Dist. Tot. (m)', '📐 Dist. Int. (m)', '🗺️ Schéma', '📝 Observations'
        ])
        
        # Set column widths - Optimiser pour les schémas
        header = self.table.horizontalHeader()
        header.resizeSection(0, 50)   # Numéro
        header.resizeSection(1, 100)  # Distance Totale
        header.resizeSection(2, 100)  # Distance Intermédiaire
        header.resizeSection(3, 450)  # Schéma - Largeur maximale pour lisibilité
        header.resizeSection(4, 200)  # Observations
        
        # Permettre le redimensionnement manuel des colonnes
        header.setSectionResizeMode(3, QHeaderView.Interactive)  # Colonne schéma redimensionnable
        header.setStretchLastSection(True)  # La dernière colonne s'étend
        
        # Ajuster la taille des cellules verticalement - Hauteur optimisée pour les schémas
        self.table.verticalHeader().setDefaultSectionSize(180)
        
        # Permettre le redimensionnement vertical des lignes
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        self.table.cellDoubleClicked.connect(self.onCellDoubleClicked)
        self.table.itemChanged.connect(self.onItemChanged)
        layout.addWidget(self.table)

    def addVignette(self):
        num = len(self.vignettes) + 1
        vignette = Vignette(num=num)
        self.vignettes.append(vignette)
        self._renumberVignettes()
        self._markAsModified()
        self.updateTable()

    def updateTable(self):
        # Désactiver temporairement les signaux pour éviter la récursion
        self.table.blockSignals(True)
        
        try:
            # Une vignette par ligne
            self.table.setRowCount(len(self.vignettes))

            # Fill table
            cumul_dist = 0
            for i, vignette in enumerate(self.vignettes):
                row = i  # Une vignette par ligne
                # Numéro
                self.table.setItem(row, 0, QTableWidgetItem(str(vignette.num)))
                
                # Distance cumulée
                cumul_dist += vignette.inter_dist
                self.table.setItem(row, 1, QTableWidgetItem(f"{int(cumul_dist)} m"))
                
                # Distance intermédiaire
                dist_item = DistanceTableItem(vignette.inter_dist)
                self.table.setItem(row, 2, dist_item)
                
                # Schéma
                diagram_item = QTableWidgetItem("")  # Item vide
                diagram_item.setFlags(diagram_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 3, diagram_item)
                
                if vignette.diagram:
                    logging.info(f"Displaying diagram for vignette {vignette.num}, SVG length: {len(vignette.diagram)}")
                    self.table.removeCellWidget(row, 3)
                    try:
                        container = self._create_svg_widget(vignette.diagram)
                        self.table.setCellWidget(row, 3, container)
                        self.table.setRowHeight(row, max(150, self.table.rowHeight(row)))
                        self.table.viewport().update(self.table.visualRect(self.table.model().index(row, 3)))
                    except Exception as e:
                        logging.error(f"SVG display failed: {e}", exc_info=True)
                        self.table.setItem(row, 3, QTableWidgetItem('[Erreur schéma]'))
                else:
                    logging.info(f"No diagram for vignette {vignette.num}")
                
                # Observations
                self.table.setItem(row, 4, QTableWidgetItem(vignette.observations))
            # Forcer le rafraîchissement de l'affichage
            self.table.viewport().update()
        finally:
            # Reactivate signals
            self.table.blockSignals(False)
    
    def _create_svg_widget(self, svg_data):
        """Create SVG widget for table cell"""
        class SVGWidget(QWidget):
            def __init__(self, svg_data):
                super().__init__()
                self.renderer = QSvgRenderer(QByteArray(svg_data.encode('utf-8')))
                layout = QVBoxLayout(self)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setAlignment(Qt.AlignCenter)
                self.label = QLabel()
                self.label.setAlignment(Qt.AlignCenter)
                self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                self.label.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.label)
                self.setMinimumHeight(1)
                self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                self._render()
            
            def resizeEvent(self, event):
                super().resizeEvent(event)
                self._render()
            
            def _render(self):
                if not self.renderer.isValid():
                    self.label.setText('SVG invalide')
                    logging.warning("Invalid SVG renderer")
                    return
                cr = self.contentsRect()
                aw = max(50, cr.width())  # Taille minimale
                ah = max(50, cr.height())
                
                # Cache image based on size
                current_size = (aw, ah)
                if hasattr(self, '_last_size') and self._last_size == current_size and hasattr(self, '_cached_pixmap'):
                    self.label.setPixmap(self._cached_pixmap)
                    return
                
                img = QImage(aw, ah, QImage.Format_ARGB32)
                img.fill(0xFFFFFFFF)  # Fond blanc au lieu de transparent
                painter = QPainter(img)
                try:
                    painter.setRenderHint(QPainter.Antialiasing)
                    self.renderer.render(painter, QRectF(0, 0, aw, ah))
                finally:
                    painter.end()
                
                self._cached_pixmap = QPixmap.fromImage(img)
                self._last_size = current_size
                self.label.setPixmap(self._cached_pixmap)
                logging.info(f"SVG rendered to {aw}x{ah} pixels")
        
        return SVGWidget(svg_data)

    def onCellDoubleClicked(self, row, column):
        # L'index de la vignette correspond directement à la ligne
        vignette_index = row
        
        if vignette_index >= len(self.vignettes):
            return
            
        if column == 3:  # Colonne Schéma (0-based: #=0, Dist.Tot=1, Dist.Int=2, Schéma=3, Obs=4)
            editor = VignetteEditor(self.vignettes[vignette_index], self)
            result = editor.exec_()
            if result == QDialog.Accepted:
                # Le SVG est déjà sauvegardé dans la vignette par l'éditeur
                self._markAsModified()
                # Forcer le rafraîchissement de l'affichage
                self.updateTable()

    def onItemChanged(self, item):
        # Si les signaux sont bloqués, ne rien faire
        if self.table.signalsBlocked():
            return
            
        row = item.row()
        col = item.column()
        
        # L'index de la vignette correspond directement à la ligne
        vignette_index = row
        
        if vignette_index >= len(self.vignettes):
            return
            
        if isinstance(item, DistanceTableItem) and col == 2:  # Distance intermédiaire column (0-based)
            self.vignettes[vignette_index].inter_dist = item.distance()
            self._markAsModified()
            self.updateTable()
        elif col == 4:  # Observations column (0-based)
            self.vignettes[vignette_index].observations = item.text()
            self._markAsModified()
            # Pas besoin de updateTable() ici car cela effacerait le texte en cours d'édition

    def deleteSelected(self):
        selected_items = self.table.selectedItems()
        vignette_indices = set()
        
        for item in selected_items:
            row = item.row()
            vignette_indices.add(row)
        
        if not vignette_indices:
            return
            
        # Remove vignettes in reverse order to maintain correct indices
        for index in sorted(vignette_indices, reverse=True):
            if index < len(self.vignettes):
                del self.vignettes[index]
        
        self._renumberVignettes()
        self._markAsModified()
        self.updateTable()

    def _renumberVignettes(self):
        """Automatically renumber all vignettes sequentially"""
        for i, vignette in enumerate(self.vignettes, 1):
            vignette.num = i
    
    def _setupAutoSave(self):
        """Setup automatic save every 5 minutes"""
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._autoSave)
        self.auto_save_timer.start(300000)  # 5 minutes = 300000 ms
    
    def _autoSave(self):
        """Perform automatic save if there are unsaved changes"""
        if self.has_unsaved_changes and self.current_filename and self.vignettes:
            try:
                self._saveToFile(self.current_filename)
                logging.info(f"Auto-save completed: {self.current_filename}")
            except Exception as e:
                logging.error(f"Auto-save failed: {e}")
    
    def _saveToFile(self, filename):
        """Save vignettes to specified file"""
        import json
        data = {
            'vignettes': [
                {
                    'num': v.num,
                    'inter_dist': v.inter_dist,
                    'observations': v.observations,
                    'diagram': v.diagram,
                    'drawing_elements': v.drawing_elements
                } for v in self.vignettes
            ]
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.has_unsaved_changes = False
    
    def _markAsModified(self):
        """Mark the document as having unsaved changes"""
        self.has_unsaved_changes = True
    
    def _checkForUpdates(self):
        """Check for application updates"""
        try:
            from update_checker import check_for_updates
            self.update_checker = check_for_updates(self)
        except ImportError:
            logging.debug("Update checker not available")

    def exportPDF(self):
        try:
            if not self.vignettes:
                QMessageBox.warning(self, "Attention", 
                                  "Aucune vignette à exporter. Ajoutez d'abord des vignettes au road book.")
                return
                
            exporter = PDFExporter(self.vignettes)
            filename = exporter.export()
            
            # Vérifier que le fichier a été créé
            if os.path.exists(filename):
                QMessageBox.information(self, "Export terminé", 
                                      f"Road book exporté avec succès vers :\n{filename}")
            else:
                QMessageBox.warning(self, "Erreur d'export", 
                                  "Le fichier PDF n'a pas pu être créé.")
                
        except Exception as e:
            # Journaliser la trace complète dans un fichier log (toujours à la racine du projet)
            try:
                import traceback
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                log_dir = os.path.join(base_dir, 'output')
                os.makedirs(log_dir, exist_ok=True)
                log_path = os.path.join(log_dir, 'export_error.log')
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write("\n=== Erreur export PDF ===\n")
                    f.write(traceback.format_exc())
            except Exception:
                log_path = '(échec de l’écriture du journal)'
            
            QMessageBox.critical(self, "Erreur d'export", 
                               f"Une erreur s'est produite lors de l'export PDF :\n{str(e)}")



    def showInfos(self):
        info_text = """
📍 ÉDITEUR DE ROAD BOOK

👨‍💻 Projet mené par Guillaume Lemiègre
Application développée par IA
📅 Version : Septembre 2025

⚖️ LICENCE ET UTILISATION :
• Logiciel Open Source
• Usage personnel et associatif autorisé
• Usage commercial strictement interdit
• Redistribution libre avec mention de l'auteur

🛠️ TECHNOLOGIES :
• Python 3.7+
• PyQt5 pour l'interface graphique
• ReportLab pour l'export PDF
• SVG pour les schémas vectoriels

🎯 UTILISATION :
• Création de roadbooks pour l'orienteering
• Multi-sport raids et compétitions
• Navigation sportive et loisir

⚠️ AVERTISSEMENT :
• Outil d'aide à la navigation uniquement
• Vérifiez toujours vos itinéraires
• L'auteur décline toute responsabilité
  en cas d'erreur de navigation

📞 SUPPORT :
• Documentation intégrée
• Logs d'erreur dans le dossier output/
• Interface intuitive et ergonomique

© 2025 Guillaume Lemiègre - Tous droits réservés
Usage commercial interdit - Open Source
        """
        
        QMessageBox.information(self, "ℹ️ Informations sur l'application", info_text)
    
    def saveRoadbook(self):
        try:
            from PyQt5.QtWidgets import QFileDialog
            import json
            
            if not self.vignettes:
                QMessageBox.warning(self, "Attention", "Aucune vignette à sauvegarder.")
                return
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Sauvegarder le roadbook", "", "Fichiers Roadbook (*.rbk)")
            
            if filename:
                self._saveToFile(filename)
                self.current_filename = filename
                QMessageBox.information(self, "Sauvegarde réussie", 
                                      f"Roadbook sauvegardé avec succès :\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur de sauvegarde", 
                               f"Erreur lors de la sauvegarde :\n{str(e)}")
    
    def openRoadbook(self):
        try:
            from PyQt5.QtWidgets import QFileDialog
            import json
            
            filename, _ = QFileDialog.getOpenFileName(
                self, "Ouvrir un roadbook", "", "Fichiers Roadbook (*.rbk)")
            
            if filename:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.vignettes = []
                for v_data in data['vignettes']:
                    vignette = Vignette(
                        num=v_data['num'],
                        inter_dist=v_data['inter_dist'],
                        observations=v_data['observations']
                    )
                    if v_data.get('diagram'):
                        elements = v_data.get('drawing_elements', [])
                        vignette.set_diagram(v_data['diagram'], elements)
                    self.vignettes.append(vignette)
                
                self._renumberVignettes()
                self.current_filename = filename
                self.has_unsaved_changes = False
                self.updateTable()
                QMessageBox.information(self, "Ouverture réussie", 
                                      f"Roadbook ouvert avec succès :\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur d'ouverture", 
                               f"Erreur lors de l'ouverture :\n{str(e)}")

def main():
    try:
        from logging_config import setup_logging
        logger = setup_logging()
        
        app = QApplication(sys.argv)
        window = RoadBookApp()
        window.show()
        logger.info("Application started successfully")
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(f"Application startup failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
