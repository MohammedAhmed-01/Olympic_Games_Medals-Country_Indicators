"""Logging configuration for console and UTC file output."""

import logging
import time
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    """Create a logger with UTC file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        log_dir = Path(__file__).resolve().parent.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        formatter = logging.Formatter(
            "%(asctime)sZ %(levelname)s %(name)s %(message)s"
        )
        formatter.converter = time.gmtime
        file_handler = logging.FileHandler(log_dir / "pipeline.log", encoding="utf-8")
        file_handler.setFormatter(formatter)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger
