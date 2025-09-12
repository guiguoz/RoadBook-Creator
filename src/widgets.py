from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox

class DistanceTableItem(QTableWidgetItem):
    def __init__(self, distance=0):
        super().__init__(f"{int(distance)} m")
        self._distance = distance

    def setData(self, role, value):
        try:
            if isinstance(value, str):
                # Remove "m" unit if present
                value = value.replace('m', '').strip()
            
            # Convert to integer
            new_distance = int(float(value))
            
            # Check that distance is positive
            if new_distance < 0:
                QMessageBox.warning(None, "Erreur", 
                    "La distance doit être positive")
                # Restore original value to maintain UI consistency
                super().setData(role, f"{self._distance} m")
                return
                
            self._distance = new_distance
            super().setData(role, f"{new_distance} m")
            
        except ValueError:
            QMessageBox.warning(None, "Erreur", 
                "Veuillez entrer un nombre entier valide")
            # Restore original value to maintain UI consistency
            super().setData(role, f"{self._distance} m")
            return

    def distance(self):
        return self._distance
