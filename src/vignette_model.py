from dataclasses import dataclass
from typing import Optional
from PyQt5.QtGui import QPixmap

@dataclass
class Vignette:
    num: int
    inter_dist: float = 0.0
    diagram: Optional[str] = None  # SVG string
    observations: str = ""
    drawing_elements: list = None  # Store drawing elements for re-editing
    
    def __post_init__(self):
        if self.drawing_elements is None:
            self.drawing_elements = []
    
    def set_diagram(self, svg_data: str, elements: list = None):
        """Set the diagram as SVG string and store drawing elements"""
        self.diagram = svg_data
        if elements is not None:
            self.drawing_elements = elements
    
    def get_diagram(self) -> Optional[str]:
        """Get the diagram as SVG string"""
        return self.diagram
    
    def get_drawing_elements(self) -> list:
        """Get the drawing elements for re-editing"""
        return self.drawing_elements or []
