from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                           QGraphicsScene, QGraphicsView, QToolBar, QAction,
                           QGridLayout, QToolButton, QComboBox, QLabel,
                           QGraphicsPathItem, QButtonGroup, QGraphicsEllipseItem,
                           QGraphicsTextItem, QColorDialog, QInputDialog, QGraphicsItem)
from PyQt5.QtGui import QPainter, QPen, QPainterPath, QTransform, QColor, QFont
from PyQt5.QtCore import Qt, QPointF, QBuffer, QIODevice, QRectF
from PyQt5.QtSvg import QSvgGenerator, QGraphicsSvgItem, QSvgRenderer
from vignette_model import Vignette
from collections import deque
import io
import math
import logging

class VignetteEditor(QDialog):
    # Constants
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 650
    SCENE_WIDTH = 750
    SCENE_HEIGHT = 400
    BALISE_RADIUS = 37
    BALISE_PEN_WIDTH = 6
    DEFAULT_LINE_WIDTHS = [3, 5, 7]
    
    def __init__(self, vignette: Vignette, parent=None):
        super().__init__(parent)
        self.vignette = vignette
        self.drawing = False
        self.last_point = None
        self.current_path = None
        self.undo_stack = deque(maxlen=50)
        self.redo_stack = deque(maxlen=50)
        self.default_cursor = Qt.ArrowCursor
        
        self.selection_mode = False
        self.selected_item = None
        self.dragging = False
        self.drag_start_pos = None
        self.item_start_pos = None
        
        self.temp_path_item = None
        
        self.text_color = QColor(Qt.black)
        self.text_font = QFont("Arial", 12)
        self.text_font.setBold(True)
        
        self.background_svg_item = None
        
        # Cache initialization
        self._cached_pen = None
        self._cached_path = QPainterPath()
        self._pen_cache = {}
        self._pen_needs_update = True
        
        # Liste des éléments éditables
        self.editable_items = []
        
        self.initUI()
        
        # Charger les éléments existants après l'initialisation de l'UI
        self.loadExistingElements()

    def initUI(self):
        self.setWindowTitle('Éditeur de Schéma')
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.setGeometry(200, 200, self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        # Utiliser les styles par défaut de Qt pour une meilleure compatibilité
        pass
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        layout.addWidget(self._createSimpleToolbar())
        layout.addWidget(self._createInfoMessage())
        layout.addWidget(self._createGraphicsView())
        layout.addLayout(self._createButtonLayout())
        
        # Ne pas charger de diagramme SVG, garder la scène éditable
        # if self.vignette.diagram:
        #     self.loadDiagram()
            
        self.freeDrawButton.setChecked(True)
        self.toggleDrawingMode()
    
    def _createSimpleToolbar(self):
        from PyQt5.QtWidgets import QWidget
        
        toolbar = QWidget()
        toolbar.setFixedHeight(120)
        
        # Layout principal vertical
        main_layout = QVBoxLayout(toolbar)
        main_layout.setSpacing(5)
        main_layout.setContentsMargins(10, 5, 10, 5)
        
        # LIGNE 1: Fonctions d'édition
        edit_layout = QHBoxLayout()
        edit_layout.setSpacing(10)
        
        self.undoButton = QPushButton('Annuler')
        self.undoButton.clicked.connect(self.undo)
        self.undoButton.setEnabled(False)
        edit_layout.addWidget(self.undoButton)
        
        self.redoButton = QPushButton('Rétablir')
        self.redoButton.clicked.connect(self.redo)
        self.redoButton.setEnabled(False)
        edit_layout.addWidget(self.redoButton)
        
        self.mainButton = QPushButton('Déplacer')
        self.mainButton.setCheckable(True)
        self.mainButton.clicked.connect(self.toggleSelectionMode)
        edit_layout.addWidget(self.mainButton)
        
        self.eraserButton = QPushButton('Effacer')
        self.eraserButton.setCheckable(True)
        self.eraserButton.clicked.connect(self.toggleEraserMode)
        edit_layout.addWidget(self.eraserButton)
        
        edit_layout.addStretch()
        main_layout.addLayout(edit_layout)
        
        # LIGNE 2: Fonctions de dessin
        draw_layout = QHBoxLayout()
        draw_layout.setSpacing(10)
        
        self.orientationGroup = QButtonGroup(self)
        
        self.freeDrawButton = QPushButton('Libre')
        self.freeDrawButton.setCheckable(True)
        self.freeDrawButton.setChecked(True)
        self.freeDrawButton.clicked.connect(self.toggleDrawingMode)
        self.orientationGroup.addButton(self.freeDrawButton)
        draw_layout.addWidget(self.freeDrawButton)
        
        self.horizontalButton = QPushButton('Horizontal')
        self.horizontalButton.setCheckable(True)
        self.horizontalButton.clicked.connect(self.toggleDrawingMode)
        self.orientationGroup.addButton(self.horizontalButton)
        draw_layout.addWidget(self.horizontalButton)
        
        self.verticalButton = QPushButton('Vertical')
        self.verticalButton.setCheckable(True)
        self.verticalButton.clicked.connect(self.toggleDrawingMode)
        self.orientationGroup.addButton(self.verticalButton)
        draw_layout.addWidget(self.verticalButton)
        
        # ComboBox type de ligne
        self.lineTypeCombo = QComboBox()
        self.lineTypeCombo.addItems([
            'Flèche épaisse', 'Flèche moyenne', 'Flèche fine',
            'Flèche pointillés épais', 'Flèche pointillés moyens', 'Flèche pointillés fins',
            'Trait épais', 'Trait moyen', 'Trait fin',
            'Pointillés épais', 'Pointillés moyens', 'Pointillés fins',
            'Route goudronnée', 'Route goudronnée avec flèche'
        ])
        self.lineTypeCombo.setMinimumWidth(180)
        draw_layout.addWidget(self.lineTypeCombo)
        
        draw_layout.addStretch()
        main_layout.addLayout(draw_layout)
        
        # LIGNE 3: Fonctions texte
        text_layout = QHBoxLayout()
        text_layout.setSpacing(10)
        
        self.baliseButton = QPushButton('Balise')
        self.baliseButton.setCheckable(True)
        self.baliseButton.clicked.connect(self.toggleBaliseMode)
        text_layout.addWidget(self.baliseButton)
        
        self.textButton = QPushButton('Texte')
        self.textButton.setCheckable(True)
        self.textButton.clicked.connect(self.toggleTextMode)
        text_layout.addWidget(self.textButton)
        
        # Taille texte
        self.textSizeCombo = QComboBox()
        self.textSizeCombo.addItems(['8', '10', '12', '14', '16', '18', '20', '24', '28', '32', '36', '48', '60', '72'])
        self.textSizeCombo.setCurrentText('12')
        self.textSizeCombo.currentTextChanged.connect(self.changeTextSize)
        self.textSizeCombo.setMaximumWidth(60)
        text_layout.addWidget(self.textSizeCombo)
        
        self.textColorButton = QPushButton('Couleur')
        self.textColorButton.clicked.connect(self.changeTextColor)
        text_layout.addWidget(self.textColorButton)
        
        # Aperçu de la couleur sélectionnée
        self.colorPreview = QLabel()
        self.colorPreview.setFixedSize(30, 25)
        self.colorPreview.setStyleSheet(f"background-color: {self.text_color.name()}; border: 1px solid #000000;")
        text_layout.addWidget(self.colorPreview)
        
        text_layout.addStretch()
        main_layout.addLayout(text_layout)
        
        return toolbar
    
    def _createInfoMessage(self):
        info_label = QLabel("💡 Pour un rendu optimal, assurez-vous que le schéma occupe entièrement l'éditeur, ou au minimum la plus grande partie de la fenêtre")
        info_label.setStyleSheet("""
            QLabel {
                background-color: #e8f4fd;
                color: #1976d2;
                padding: 8px;
                border: 1px solid #2196f3;
                border-radius: 4px;
                font-size: 11px;
                font-style: italic;
            }
        """)
        info_label.setWordWrap(True)
        return info_label
    
    def _createGraphicsView(self):
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, self.SCENE_WIDTH, self.SCENE_HEIGHT)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setFixedSize(self.SCENE_WIDTH, self.SCENE_HEIGHT)
        
        self.view.setMouseTracking(True)
        self.view.viewport().installEventFilter(self)
        return self.view
    
    def _createButtonLayout(self):
        btnLayout = QHBoxLayout()
        btnLayout.setSpacing(15)
        btnLayout.setContentsMargins(0, 10, 0, 0)
        
        btnCancel = QPushButton('Annuler', self)
        btnCancel.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: 2px solid #d32f2f;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                min-width: 80px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        btnCancel.clicked.connect(self.reject)
        
        btnOk = QPushButton('Valider', self)
        btnOk.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: 2px solid #45a049;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                min-width: 80px;
                min-height: 32px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        btnOk.clicked.connect(self.accept)
        
        btnLayout.addStretch()
        btnLayout.addWidget(btnCancel)
        btnLayout.addWidget(btnOk)
        return btnLayout
            
    def _deactivateAllModes(self):
        buttons = [self.mainButton, self.eraserButton, self.freeDrawButton, 
                   self.horizontalButton, self.verticalButton, self.baliseButton, self.textButton]
        for button in buttons:
            button.setChecked(False)
        self.selection_mode = False
        
    def toggleSelectionMode(self):
        if self.mainButton.isChecked():
            self._deactivateAllModes()
            self.mainButton.setChecked(True)
            self.selection_mode = True
            self.view.setCursor(Qt.ArrowCursor)
        else:
            self.selection_mode = False
            self.view.setCursor(self.default_cursor)
            
    def toggleEraserMode(self):
        if self.eraserButton.isChecked():
            self._deactivateAllModes()
            self.eraserButton.setChecked(True)
            self.view.setCursor(Qt.ArrowCursor)
        else:
            self.view.setCursor(self.default_cursor)

    def toggleDrawingMode(self):
        current_checked = self.orientationGroup.checkedButton()
        if current_checked:
            self._deactivateAllModes()
            current_checked.setChecked(True)
        else:
            self.view.setCursor(self.default_cursor)
            
    def toggleBaliseMode(self):
        if self.baliseButton.isChecked():
            self._deactivateAllModes()
            self.baliseButton.setChecked(True)
            self.view.setCursor(Qt.CrossCursor)
        else:
            self.view.setCursor(self.default_cursor)
            
    def toggleTextMode(self):
        if self.textButton.isChecked():
            self._deactivateAllModes()
            self.textButton.setChecked(True)
            self.view.setCursor(Qt.IBeamCursor)
        else:
            self.view.setCursor(self.default_cursor)
            
    def changeTextColor(self):
        color = QColorDialog.getColor(self.text_color, self, "Choisir la couleur du texte")
        if color.isValid():
            self.text_color = color
            # Mettre à jour l'aperçu de couleur
            self.colorPreview.setStyleSheet(f"background-color: {self.text_color.name()}; border: 1px solid #000000;")
            
    def changeTextSize(self, size_str):
        new_size = int(size_str)
        self.text_font.setPointSize(new_size)
        
    def createBalise(self, center: QPointF):
        rect = QRectF(center.x() - self.BALISE_RADIUS, center.y() - self.BALISE_RADIUS, 
                      self.BALISE_RADIUS * 2, self.BALISE_RADIUS * 2)
        
        circle = QGraphicsEllipseItem(rect)
        pen = QPen(Qt.magenta)
        pen.setWidth(self.BALISE_PEN_WIDTH)
        circle.setPen(pen)
        circle.setBrush(Qt.transparent)
        circle.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        
        self.scene.addItem(circle)
        self.undo_stack.append(circle)
        self.editable_items.append(circle)
        self.redo_stack.clear()
        self.updateUndoRedoButtons()
        logging.info(f"Balise created at {center}")
        
    def createText(self, pos: QPointF):
        text, ok = QInputDialog.getText(self, "Ajouter du texte", "Entrez le texte:")
        if not ok or not text:
            return
            
        text_item = QGraphicsTextItem(text)
        text_item.setPos(pos)
        text_item.setDefaultTextColor(self.text_color)
        text_item.setFont(self.text_font)
        text_item.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        
        self.scene.addItem(text_item)
        self.undo_stack.append(text_item)
        self.editable_items.append(text_item)
        self.redo_stack.clear()
        self.updateUndoRedoButtons()
        logging.info(f"Text created: {text}")
            
    def eventFilter(self, obj, event):
        if obj == self.view.viewport():
            if event.type() == event.MouseButtonPress:
                self.viewportMousePressEvent(event)
                return True
            elif event.type() == event.MouseMove:
                self.viewportMouseMoveEvent(event)
                return True
            elif event.type() == event.MouseButtonRelease:
                self.viewportMouseReleaseEvent(event)
                return True
        return super().eventFilter(obj, event)
            
    def viewportMousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.view.mapToScene(event.pos())
            
            if self.selection_mode:
                item = self.scene.itemAt(pos, self.view.transform())
                if item and isinstance(item, QGraphicsItem) and not isinstance(item, QGraphicsSvgItem):
                    self.selected_item = item
                    self.dragging = True
                    self.drag_start_pos = pos
                    self.item_start_pos = item.pos()
                    self.view.setCursor(Qt.ClosedHandCursor)
                else:
                    self.selected_item = None
                    self.dragging = False
                return
                
            if self.baliseButton.isChecked():
                self.createBalise(pos)
                return
                
            if self.textButton.isChecked():
                self.createText(pos)
                return
                
            if self.eraserButton.isChecked():
                item = self.scene.itemAt(pos, self.view.transform())
                if item and isinstance(item, QGraphicsItem) and not isinstance(item, QGraphicsSvgItem):
                    self.scene.removeItem(item)
                    # More efficient removal from deques
                    try:
                        self.undo_stack.remove(item)
                    except ValueError:
                        pass
                    try:
                        self.redo_stack.remove(item)
                    except ValueError:
                        pass
                    self.updateUndoRedoButtons()
                return
            
            self.drawing = True
            self.last_point = pos
            self.current_path = QPainterPath()
            self.current_path.moveTo(self.last_point)
            self._pen_needs_update = True
            
    def viewportMouseMoveEvent(self, event):
        pos = self.view.mapToScene(event.pos())
        
        if self.selection_mode:
            if self.dragging and self.selected_item:
                delta = pos - self.drag_start_pos
                new_pos = self.item_start_pos + delta
                self.selected_item.setPos(new_pos)
                return
            else:
                # Cache itemAt result to avoid repeated calls
                item = self.scene.itemAt(pos, self.view.transform())
                if item and isinstance(item, QGraphicsItem) and not isinstance(item, QGraphicsSvgItem):
                    self.view.setCursor(Qt.OpenHandCursor)
                else:
                    self.view.setCursor(Qt.ArrowCursor)
            return
            
        if self.eraserButton.isChecked():
            item = self.scene.itemAt(pos, self.view.transform())
            if item and isinstance(item, QGraphicsItem) and not isinstance(item, QGraphicsSvgItem):
                self.view.setCursor(Qt.PointingHandCursor)
            else:
                self.view.setCursor(Qt.ArrowCursor)
            return
            
        if not self.drawing:
            return
            
        current_point = pos
        
        if self.temp_path_item:
            self.scene.removeItem(self.temp_path_item)
            self.temp_path_item = None
            
        # Appliquer les contraintes d'orientation pour l'aperçu
        preview_end = current_point
        if self.horizontalButton.isChecked():
            preview_end = QPointF(current_point.x(), self.last_point.y())
        elif self.verticalButton.isChecked():
            preview_end = QPointF(self.last_point.x(), current_point.y())
        
        line_type = self.lineTypeCombo.currentText()
        
        if 'Route goudronnée' in line_type:
            # Aperçu spécial pour la route goudronnée
            self._cached_path = self.createRoadPath(self.last_point, preview_end, 'avec flèche' in line_type)
            pen = QPen(Qt.black, 3)
        else:
            # Aperçu normal pour les autres types
            self._cached_path.clear()
            self._cached_path.moveTo(self.last_point)
            self._cached_path.lineTo(preview_end)
            if self._pen_needs_update:
                self._cached_pen = self.createPen()
                self._pen_needs_update = False
            pen = self._cached_pen
            
        self.temp_path_item = self.scene.addPath(self._cached_path, pen)
        
    def viewportMouseReleaseEvent(self, event):
        if self.selection_mode and self.dragging:
            self.dragging = False
            self.view.setCursor(Qt.ArrowCursor)
            return
        
        if not self.drawing:
            return
        
        self.drawing = False
        end_point = self.view.mapToScene(event.pos())
        
        self.createArrow(self.last_point, end_point)
        
    def createPen(self):
        style = self.lineTypeCombo.currentText()
        
        # Check cache first
        if style in self._pen_cache:
            return self._pen_cache[style]
        
        pen = QPen(Qt.black)
        
        if 'Pointillés' in style or 'pointillés' in style:
            pen.setStyle(Qt.DashLine)
        else:
            pen.setStyle(Qt.SolidLine)
            
        # Use constants for line widths
        if 'fin' in style.lower():
            pen.setWidth(self.DEFAULT_LINE_WIDTHS[0])
        elif 'moyen' in style.lower():
            pen.setWidth(self.DEFAULT_LINE_WIDTHS[1])

        else:
            pen.setWidth(self.DEFAULT_LINE_WIDTHS[2])
        
        # Cache the pen
        self._pen_cache[style] = pen
        return pen
        
    def createArrow(self, start: QPointF, end: QPointF) -> None:
        if self.horizontalButton.isChecked():
            end = QPointF(end.x(), start.y())
        elif self.verticalButton.isChecked():
            end = QPointF(start.x(), end.y())
        
        line_type = self.lineTypeCombo.currentText()
        
        if 'Route goudronnée' in line_type:
            self.createRoad(start, end, 'avec flèche' in line_type)
            return
        
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        angle = math.atan2(dy, dx)

        path = QPainterPath()
        path.moveTo(start)
        path.lineTo(end)
        
        is_arrow = 'Flèche' in line_type
        
        if is_arrow:
            if 'épaisse' in line_type:
                arrow_size = 20
            elif 'moyenne' in line_type:
                arrow_size = 15
            else:
                arrow_size = 10
                
            arrow_angle = math.pi / 6
            
            # Pre-calculate trigonometric values
            cos_minus = math.cos(angle - arrow_angle)
            sin_minus = math.sin(angle - arrow_angle)
            cos_plus = math.cos(angle + arrow_angle)
            sin_plus = math.sin(angle + arrow_angle)
            
            point1 = QPointF(
                end.x() - arrow_size * cos_minus,
                end.y() - arrow_size * sin_minus
            )
            point2 = QPointF(
                end.x() - arrow_size * cos_plus,
                end.y() - arrow_size * sin_plus
            )
            
            # Pour les flèches pointillées, dessiner la pointe avec un trait plein
            if 'pointillés' in line_type:
                # Dessiner d'abord le corps avec pointillés
                pen = self.createPen()
                item = self.scene.addPath(path, pen)
                item.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
                self.undo_stack.append(item)
                
                # Puis dessiner la pointe avec trait plein plus épais
                arrow_path = QPainterPath()
                arrow_path.moveTo(end)
                arrow_path.lineTo(point1)
                arrow_path.moveTo(end)
                arrow_path.lineTo(point2)
                
                solid_pen = QPen(Qt.black)
                # Rendre la pointe plus épaisse pour les flèches pointillées épaisses
                arrow_width = pen.width() + 2 if 'épais' in line_type else pen.width()
                solid_pen.setWidth(arrow_width)
                arrow_item = self.scene.addPath(arrow_path, solid_pen)
                arrow_item.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
                self.undo_stack.append(arrow_item)
                
                self.redo_stack.clear()
                self.updateUndoRedoButtons()
                
                if self.temp_path_item:
                    self.scene.removeItem(self.temp_path_item)
                    self.temp_path_item = None
                return
            else:
                path.lineTo(point1)
                path.moveTo(end)
                path.lineTo(point2)
        
        pen = self.createPen()
        
        item = self.scene.addPath(path, pen)
        item.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        
        self.undo_stack.append(item)
        self.editable_items.append(item)
        self.redo_stack.clear()
        
        self.updateUndoRedoButtons()
        
        if self.temp_path_item:
            self.scene.removeItem(self.temp_path_item)
            self.temp_path_item = None
            
    def createRoadPreview(self, start: QPointF, end: QPointF):
        """Crée un aperçu de la route pendant le dessin"""
        path = self.createRoadPath(start, end)
        pen = QPen(Qt.black, 2)
        return self.scene.addPath(path, pen)
        
    def createRoad(self, start: QPointF, end: QPointF, with_arrow: bool = True):
        """Crée une route goudronnée avec lignes parallèles et optionnellement une flèche"""
        path = self.createRoadPath(start, end, with_arrow)
        pen = QPen(Qt.black, 3)
        
        item = self.scene.addPath(path, pen)
        item.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
        
        self.undo_stack.append(item)
        self.editable_items.append(item)
        self.redo_stack.clear()
        self.updateUndoRedoButtons()
        
        # Nettoyer l'aperçu temporaire
        if self.temp_path_item:
            self.scene.removeItem(self.temp_path_item)
            self.temp_path_item = None
        
    def createRoadPath(self, start: QPointF, end: QPointF, with_arrow: bool = True) -> QPainterPath:
        """Crée le chemin d'une route avec deux traits parallèles et optionnellement un triangle"""
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 1:
            return QPainterPath()
            
        angle = math.atan2(dy, dx)
        
        # Espacement des lignes parallèles (taille trait fin)
        spacing = 6
        px = -math.sin(angle) * spacing
        py = math.cos(angle) * spacing
        
        path = QPainterPath()
        
        # Deux lignes parallèles
        path.moveTo(start.x() + px, start.y() + py)
        path.lineTo(end.x() + px, end.y() + py)
        
        path.moveTo(start.x() - px, start.y() - py)
        path.lineTo(end.x() - px, end.y() - py)
        
        # Triangle fermé en pointe seulement si demandé
        if with_arrow:
            triangle_length = 20
            triangle_width = 12
            
            # Point de la pointe du triangle
            tip_x = end.x() + triangle_length * math.cos(angle)
            tip_y = end.y() + triangle_length * math.sin(angle)
            
            # Points de la base du triangle
            base_px = -math.sin(angle) * triangle_width
            base_py = math.cos(angle) * triangle_width
            
            base1_x = end.x() + base_px
            base1_y = end.y() + base_py
            base2_x = end.x() - base_px
            base2_y = end.y() - base_py
            
            # Dessiner le triangle fermé
            path.moveTo(base1_x, base1_y)
            path.lineTo(tip_x, tip_y)
            path.lineTo(base2_x, base2_y)
            path.lineTo(base1_x, base1_y)
        
        return path

    def undo(self):
        if self.undo_stack:
            item = self.undo_stack.pop()
            self.scene.removeItem(item)
            self.redo_stack.append(item)
            self.updateUndoRedoButtons()
            
    def redo(self):
        if self.redo_stack:
            item = self.redo_stack.pop()
            self.scene.addItem(item)
            self.undo_stack.append(item)
            self.updateUndoRedoButtons()
            
    def updateUndoRedoButtons(self):
        self.undoButton.setEnabled(bool(self.undo_stack))
        self.redoButton.setEnabled(bool(self.redo_stack))
    
    def accept(self):
        svg_data = self.sceneToSVG()
        elements_data = self.saveElementsData()
        logging.info(f"Saving diagram - SVG length: {len(svg_data)}, Elements: {len(elements_data)}")
        self.vignette.set_diagram(svg_data, elements_data)
        super().accept()

    def sceneToSVG(self) -> str:
        try:
            # Vérifier s'il y a des éléments dans la scène
            items = [item for item in self.scene.items() if not isinstance(item, QGraphicsSvgItem)]
            if not items:
                logging.info("No drawable items in scene")
                return ""
            
            rect = self.scene.sceneRect()
            
            buffer = QBuffer()
            buffer.open(QBuffer.ReadWrite)
            generator = QSvgGenerator()
            generator.setOutputDevice(buffer)
            generator.setSize(rect.size().toSize())
            generator.setViewBox(rect)
            
            painter = QPainter()
            if not painter.begin(generator):
                logging.error("Failed to begin painting")
                return ""
            
            try:
                painter.setRenderHint(QPainter.Antialiasing)
                self.scene.render(painter, rect, rect)
            finally:
                painter.end()
            
            buffer.close()
            svg_data = buffer.data().data().decode('utf-8')
            
            if len(svg_data) < 100:  # SVG trop petit = probablement vide
                logging.warning(f"Generated SVG seems empty: {len(svg_data)} chars")
                return ""
                
            logging.info(f"SVG generated successfully: {len(svg_data)} chars")
            return svg_data
            
        except Exception as e:
            logging.error(f"Erreur génération SVG: {e}", exc_info=True)
            return ""
    
    def loadDiagram(self):
        if not self.vignette.diagram:
            logging.info("No existing diagram to load")
            return
            
        logging.info(f"Loading existing diagram, length: {len(self.vignette.diagram)}")
        try:
            renderer = QSvgRenderer(self.vignette.diagram.encode('utf-8'))
            if renderer.isValid():
                logging.info("Valid SVG, creating item")
                svg_item = QGraphicsSvgItem()
                svg_item.setSharedRenderer(renderer)
                svg_item.setZValue(-1000)
                svg_item.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
                self.scene.addItem(svg_item)
                self.background_svg_item = svg_item
                self.editable_items.append(svg_item)  # Ajouter à la liste éditable
                
                vb = renderer.viewBoxF()
                if vb.width() > 0 and vb.height() > 0:
                    self.scene.setSceneRect(vb)
                    logging.info(f"SceneRect set: {vb}")
                else:
                    logging.warning("Invalid ViewBox, using default size")
            else:
                logging.warning("Invalid SVG")
        except Exception as e:
            logging.error(f"Error loading SVG: {e}", exc_info=True)
    
    def saveElementsData(self) -> list:
        """Save all drawing elements data for re-editing"""
        elements = []
        for item in self.scene.items():
            if isinstance(item, QGraphicsPathItem):
                # Sérialiser le path en points
                path_points = []
                path = item.path()
                for i in range(path.elementCount()):
                    element = path.elementAt(i)
                    path_points.append({
                        'type': element.type,
                        'x': element.x,
                        'y': element.y
                    })
                elements.append({
                    'type': 'path',
                    'path_points': path_points,
                    'pen_color': item.pen().color().name(),
                    'pen_width': item.pen().width(),
                    'pen_style': item.pen().style(),
                    'pos': [item.pos().x(), item.pos().y()]
                })
            elif isinstance(item, QGraphicsEllipseItem):
                elements.append({
                    'type': 'ellipse',
                    'rect': [item.rect().x(), item.rect().y(), item.rect().width(), item.rect().height()],
                    'pen_color': item.pen().color().name(),
                    'pen_width': item.pen().width(),
                    'pos': [item.pos().x(), item.pos().y()]
                })
            elif isinstance(item, QGraphicsTextItem):
                elements.append({
                    'type': 'text',
                    'text': item.toPlainText(),
                    'font_family': item.font().family(),
                    'font_size': item.font().pointSize(),
                    'font_bold': item.font().bold(),
                    'color': item.defaultTextColor().name(),
                    'pos': [item.pos().x(), item.pos().y()]
                })
        return elements
    
    def loadExistingElements(self):
        """Load existing drawing elements for re-editing"""
        elements = self.vignette.get_drawing_elements()
        if not elements:
            return
            
        for element_data in elements:
            try:
                if element_data['type'] == 'path':
                    path = QPainterPath()
                    for point_data in element_data['path_points']:
                        if point_data['type'] == 0:
                            path.moveTo(point_data['x'], point_data['y'])
                        elif point_data['type'] == 1:
                            path.lineTo(point_data['x'], point_data['y'])
                    
                    item = QGraphicsPathItem(path)
                    pen = QPen(QColor(element_data['pen_color']))
                    pen.setWidth(element_data['pen_width'])
                    pen.setStyle(element_data['pen_style'])
                    item.setPen(pen)
                    item.setPos(element_data['pos'][0], element_data['pos'][1])
                    item.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
                    self.scene.addItem(item)
                    self.editable_items.append(item)
                elif element_data['type'] == 'ellipse':
                    rect_data = element_data['rect']
                    rect = QRectF(rect_data[0], rect_data[1], rect_data[2], rect_data[3])
                    item = QGraphicsEllipseItem(rect)
                    pen = QPen(QColor(element_data['pen_color']))
                    pen.setWidth(element_data['pen_width'])
                    item.setPen(pen)
                    item.setPos(element_data['pos'][0], element_data['pos'][1])
                    item.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
                    self.scene.addItem(item)
                    self.editable_items.append(item)
                elif element_data['type'] == 'text':
                    item = QGraphicsTextItem(element_data['text'])
                    font = QFont(element_data['font_family'], element_data['font_size'])
                    font.setBold(element_data['font_bold'])
                    item.setFont(font)
                    item.setDefaultTextColor(QColor(element_data['color']))
                    item.setPos(element_data['pos'][0], element_data['pos'][1])
                    item.setFlags(QGraphicsItem.ItemIsMovable | QGraphicsItem.ItemIsSelectable)
                    self.scene.addItem(item)
                    self.editable_items.append(item)
            except Exception as e:
                logging.error(f"Error loading element: {e}")