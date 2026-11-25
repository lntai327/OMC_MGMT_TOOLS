from datetime import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path
import sys
import time
from typing import Optional

from app.core.config import settings
from app.core.timezone import APP_TIMEZONE

# Default format for logs (matching TimestampMixin / now_vietnam timezone)
DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] [%(name)s]: %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_shared_file_handler: Optional["MultiProcessTimedRotatingFileHandler"] = None


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


class MultiProcessTimedRotatingFileHandler(TimedRotatingFileHandler):
    """TimedRotatingFileHandler that safely handles multi-process and multi-container logging:
    1. Inode / Stat Watching: Checks if the file on disk was renamed or rotated by another process/container
       (like WatchedFileHandler). If so, it immediately closes the stale stream and re-opens the active base file.
    2. Safe Rollover: Verifies file mtime before rotating to prevent multiple processes from cascading rotations.
    3. Auto Flush: Flushes after every log write so logs appear in app.log immediately in real-time.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_stat: Optional[os.stat_result] = None
        if self.stream and hasattr(self.stream, "fileno"):
            try:
                self._last_stat = os.fstat(self.stream.fileno())
            except Exception:
                self._last_stat = None

    def _open(self):
        stream = super()._open()
        if hasattr(stream, "fileno"):
            try:
                self._last_stat = os.fstat(stream.fileno())
            except Exception:
                self._last_stat = None
        return stream

    def emit(self, record: logging.LogRecord) -> None:
        try:
            # 1. Check if the active log file on disk has changed (rotated or recreated by another process)
            if self.stream is not None:
                try:
                    sres = os.stat(self.baseFilename)
                except FileNotFoundError:
                    sres = None

                if sres is None or (
                    self._last_stat is not None
                    and (sres.st_ino != self._last_stat.st_ino or sres.st_dev != self._last_stat.st_dev)
                ):
                    if self.stream is not None:
                        try:
                            self.stream.flush()
                            self.stream.close()
                        except Exception:
                            pass
                        self.stream = None
                    self.stream = self._open()

            # 2. Check if rollover interval has arrived
            if self.shouldRollover(record):
                self.doRollover()

            super().emit(record)

            # 3. Always flush stream so writes appear on host immediately
            if self.stream and hasattr(self.stream, "flush"):
                self.stream.flush()
        except Exception:
            self.handleError(record)

    def doRollover(self) -> None:
        if self.stream is not None:
            try:
                self.stream.flush()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

        currentTime = int(time.time())
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
        dfn = self.rotation_filename(
            self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
        )

        try:
            if os.path.exists(self.baseFilename):
                stat_base = os.stat(self.baseFilename)
                # Only rotate if the current file is actually older than rollover window
                # and another process hasn't already created a fresh file today
                if stat_base.st_mtime < self.rolloverAt:
                    if not os.path.exists(dfn):
                        try:
                            self.rotate(self.baseFilename, dfn)
                        except (FileNotFoundError, OSError):
                            pass
        except Exception:
            pass

        if self.backupCount > 0:
            try:
                for s in self.getFilesToDelete():
                    try:
                        os.remove(s)
                    except OSError:
                        pass
            except Exception:
                pass

        if not self.delay:
            self.stream = self._open()

        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        self.rolloverAt = newRolloverAt


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
) -> MultiProcessTimedRotatingFileHandler:
    """Returns a shared MultiProcessTimedRotatingFileHandler writing to settings.LOGS_PATH/app.log."""
    global _shared_file_handler
    if _shared_file_handler is None:
        log_dir = settings.LOGS_PATH
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception as e:
            sys.stdout.write(f"ERROR: Unable to create log directory {log_dir}: {e}\n")

        log_file_path = os.path.join(log_dir, log_file_name)
        formatter = TimezoneFormatter(fmt=fmt, datefmt=datefmt)

        _shared_file_handler = MultiProcessTimedRotatingFileHandler(
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
