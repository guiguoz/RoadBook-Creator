import requests
import json
import logging
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal

class UpdateChecker(QThread):
    update_available = pyqtSignal(str, str)  # version, download_url
    
    def __init__(self):
        super().__init__()
        self.current_version = "1.0.0"
        self.update_url = "https://raw.githubusercontent.com/username/roadbook-app/main/version.json"
    
    def run(self):
        try:
            response = requests.get(self.update_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("version", "1.0.0")
                download_url = data.get("download_url", "")
                
                if self._is_newer_version(latest_version):
                    self.update_available.emit(latest_version, download_url)
        except Exception as e:
            logging.debug(f"Update check failed: {e}")
    
    def _is_newer_version(self, latest):
        current = [int(x) for x in self.current_version.split('.')]
        latest_parts = [int(x) for x in latest.split('.')]
        return latest_parts > current

def check_for_updates(parent=None):
    """Check for updates and show notification"""
    checker = UpdateChecker()
    
    def on_update_available(version, url):
        reply = QMessageBox.question(
            parent,
            "🔄 Mise à jour disponible",
            f"Une nouvelle version ({version}) est disponible !\n\n"
            f"Voulez-vous télécharger la mise à jour ?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            import webbrowser
            webbrowser.open(url)
    
    checker.update_available.connect(on_update_available)
    checker.start()
    return checker