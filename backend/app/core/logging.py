from datetime import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path
import sys
from typing import Optional

from app.core.config import settings
from app.core.timezone import APP_TIMEZONE

# Default format for logs (matching TimestampMixin / now_vietnam timezone)
DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_shared_file_handler: Optional[TimedRotatingFileHandler] = None


class TimezoneFormatter(logging.Formatter):
    """Custom Formatter that outputs log timestamps in the Vietnam timezone (Asia/Ho_Chi_Minh / GMT+7),
    matching TimestampMixin and now_vietnam().
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
    ):
        super().__init__(fmt=fmt, datefmt=datefmt)

    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        # Convert record.created timestamp to timezone-aware datetime in Asia/Ho_Chi_Minh
        dt = datetime.fromtimestamp(record.created, tz=APP_TIMEZONE)
        df = datefmt or self.datefmt
        if df == "iso":
            return dt.isoformat()
        return dt.strftime(df or DEFAULT_DATE_FORMAT)


def get_shared_file_handler(
    log_file_name: str = "app.log",
    when: str = "midnight",
    interval: int = 1,
    backup_count: int = 30,
    file_level: int = logging.INFO,
    file_encoding: str = "utf-8",
    delay: bool = False,
    utc: bool = False,
    fmt: str = DEFAULT_LOG_FORMAT,
    datefmt: str = DEFAULT_DATE_FORMAT,
) -> TimedRotatingFileHandler:
    """Returns a shared TimedRotatingFileHandler writing to settings.LOGS_PATH/app.log."""
    global _shared_file_handler
    if _shared_file_handler is None:
        log_dir = settings.LOGS_PATH
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception as e:
            sys.stdout.write(f"ERROR: Unable to create log directory {log_dir}: {e}\n")

        log_file_path = os.path.join(log_dir, log_file_name)
        formatter = TimezoneFormatter(fmt=fmt, datefmt=datefmt)

        _shared_file_handler = TimedRotatingFileHandler(
            log_file_path,
            when=when,
            interval=interval,
            backupCount=backup_count,
            encoding=file_encoding,
            delay=delay,
            utc=utc,
        )
        _shared_file_handler.setFormatter(formatter)
        _shared_file_handler.setLevel(file_level)

    return _shared_file_handler


def setup_app_logging():
    """Configures root logger, uvicorn, uvicorn.access, uvicorn.error,
    and fastapi loggers to write all access and error logs to app.log with TimezoneFormatter.
    """
    file_handler = get_shared_file_handler()

    target_loggers = [
        logging.getLogger(),            # Root logger
        logging.getLogger("uvicorn"),
        logging.getLogger("uvicorn.access"),
        logging.getLogger("uvicorn.error"),
        logging.getLogger("fastapi"),
        logging.getLogger("app_logger"),
    ]

    for lg in target_loggers:
        if lg.level > logging.INFO or lg.level == logging.NOTSET:
            lg.setLevel(logging.INFO)

        # Attach shared file handler if not already attached
        has_file_handler = any(
            isinstance(h, TimedRotatingFileHandler)
            and getattr(h, "baseFilename", None) == getattr(file_handler, "baseFilename", None)
            for h in lg.handlers
        )
        if not has_file_handler:
            lg.addHandler(file_handler)

        # Update existing console handlers with TimezoneFormatter
        for h in lg.handlers:
            if isinstance(h, logging.StreamHandler) and not isinstance(h.formatter, TimezoneFormatter):
                h.setFormatter(TimezoneFormatter(fmt=DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT))


def get_logger(
    name: str = "app_logger",
    log_file_name: str = "app.log",
    when: str = "midnight",
    interval: int = 1,
    backup_count: int = 30,
    file_level: int = logging.INFO,
    console_level: int = logging.INFO,
    fmt: str = DEFAULT_LOG_FORMAT,
    datefmt: str = DEFAULT_DATE_FORMAT,
    *,
    file_encoding: str = "utf-8",
    force: bool = False,
    delay: bool = False,
    utc: bool = False,
) -> logging.Logger:
    """
    Returns a configured logger writing to both Console (stdout) and Rotating File,
    with timestamps converted to Vietnam Timezone (Asia/Ho_Chi_Minh / GMT+7).
    Log files are stored by default under settings.LOGS_PATH (storage/logs/).
    """
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

        formatter = TimezoneFormatter(fmt=fmt, datefmt=datefmt)

        # 1. Timed Rotating File Handler (shared)
        file_handler = get_shared_file_handler(
            log_file_name=log_file_name,
            when=when,
            interval=interval,
            backup_count=backup_count,
            file_level=file_level,
            file_encoding=file_encoding,
            delay=delay,
            utc=utc,
            fmt=fmt,
            datefmt=datefmt,
        )
        if file_handler not in logger.handlers:
            logger.addHandler(file_handler)

        # 2. Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(console_level)
        logger.addHandler(console_handler)

    return logger
