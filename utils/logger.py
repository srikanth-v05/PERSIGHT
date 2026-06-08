
import logging
import sys
from logging.handlers import RotatingFileHandler
import os


class _MaxLevelFilter(logging.Filter):
    def __init__(self, max_level):
        super().__init__()
        self._max_level = max_level

    def filter(self, record):
        return record.levelno <= self._max_level


def setup_logger(name: str = "PERSIGHT", log_file: str = "app.log", level: int = logging.INFO) -> logging.Logger:
    """Configures and returns a logger instance."""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler for info/debug messages
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.addFilter(_MaxLevelFilter(logging.INFO))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Alert handler for warnings/errors
    alert_handler = logging.StreamHandler(sys.stderr)
    alert_handler.setLevel(logging.WARNING)
    alert_handler.setFormatter(formatter)
    logger.addHandler(alert_handler)

    # File Handler
    try:
        max_bytes = int(os.getenv("LOG_MAX_BYTES", str(5 * 1024 * 1024)))
        backup_count = int(os.getenv("LOG_BACKUP_COUNT", "10"))
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to setup file logging: {e}")

    return logger

# Default logger instance
logger = setup_logger()
