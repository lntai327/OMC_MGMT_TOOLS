import logging
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path
import sys
from typing import Optional

from app.core.config import settings

# Default format for logs
DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"


def get_logger(
    name: str = "app_logger",
    log_file_name: str = "app.log",
    when: str = "midnight",
    interval: int = 1,
    backup_count: int = 30,
    file_level: int = logging.INFO,
    console_level: int = logging.INFO,
    fmt: str = DEFAULT_LOG_FORMAT,
    *,
    file_encoding: str = "utf-8",
    force: bool = False,
    delay: bool = False,
    utc: bool = True,
) -> logging.Logger:
    """
    Returns a configured logger writing to both Console (stdout) and Rotating File.
    Log files are stored by default under settings.LOGS_PATH (storage/logs/).
    """
    log_dir = settings.LOGS_PATH
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception as e:
        sys.stdout.write(f"ERROR: Unable to create log directory {log_dir}: {e}\n")

    log_file_path = os.path.join(log_dir, log_file_name)

    logger = logging.getLogger(name)
    logger.setLevel(min(file_level, console_level))
    logger.propagate = False

    # Avoid adding duplicate handlers on multiple get_logger calls
    if not logger.handlers or force:
        if force:
            for h in list(logger.handlers):
                try:
                    logger.removeHandler(h)
                    h.close()
                except Exception:
                    pass

        formatter = logging.Formatter(fmt)

        # 1. Timed Rotating File Handler
        try:
            file_handler = TimedRotatingFileHandler(
                log_file_path,
                when=when,
                interval=interval,
                backupCount=backup_count,
                encoding=file_encoding,
                delay=delay,
                utc=utc,
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(file_level)
            logger.addHandler(file_handler)
        except Exception as e:
            sys.stdout.write(f"ERROR: Unable to setup TimedRotatingFileHandler for {log_file_path}: {e}\n")

        # 2. Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(console_level)
        logger.addHandler(console_handler)

    return logger

