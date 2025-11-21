# utils/logger.py

"""
Logger setup module for the application.
Ensures compatibility with Python < 3.9 by avoiding 'encoding' in basicConfig.
"""

import logging

# Create a logger instance
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Prevent adding multiple handlers if module is reloaded
if not logger.handlers:
    file_handler = logging.FileHandler('app.log', encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
