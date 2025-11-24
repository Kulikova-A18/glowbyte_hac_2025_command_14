# modules/logger.py
"""
Centralized logger that writes logs to the 'log/' directory.
Automatically creates the directory and uses daily log files.
"""

import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


class AppLogger:
    _instance = None
    _logger = None

    def __new__(cls, name="CoalFireApp"):
        if cls._instance is None:
            cls._instance = super(AppLogger, cls).__new__(cls)
            cls._instance._init_logger(name)
        return cls._instance

    def _init_logger(self, name: str):
        """Initializes the logger with file and console handlers."""
        if self._logger is not None:
            return

        # Create log directory
        log_dir = "log"
        os.makedirs(log_dir, exist_ok=True)

        # Logger setup
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.INFO)

        # Avoid duplicate handlers if module is reloaded
        if self._logger.handlers:
            return

        # Formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # File handler (rotates daily)
        log_file = os.path.join(log_dir, "app.log")
        file_handler = TimedRotatingFileHandler(
            filename=log_file,
            when="midnight",
            interval=1,
            backupCount=30,  # Keep logs for 30 days
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y-%m-%d"  # e.g., app.log.2025-11-24

        # Console handler (optional, can be removed for production)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Add handlers
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)

    def get_logger(self) -> logging.Logger:
        return self._logger


# Convenience function for easy access
def get_app_logger(name: str = "CoalFireApp") -> logging.Logger:
    return AppLogger(name).get_logger()
