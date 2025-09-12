import logging
import os
from datetime import datetime

_logging_setup = False

def setup_logging():
    """Configure logging for the roadbook application"""
    global _logging_setup
    
    # Prevent duplicate handler registration
    if _logging_setup:
        return logging.getLogger(__name__)
    
    # Create logs directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    log_dir = os.path.join(base_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f'roadbook_{timestamp}.log')
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    # Set specific loggers to appropriate levels
    logging.getLogger('PyQt5').setLevel(logging.WARNING)
    logging.getLogger('reportlab').setLevel(logging.WARNING)
    
    _logging_setup = True
    return logging.getLogger(__name__)