import logging
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path
import sys
from typing import Optional

class LoggerUtil:
    @staticmethod
    def get_logger(
        name: str = "app_logger",
        log_file_path: Optional[str] = None,
        when: str = "midnight",
        interval: int = 1,
        backup_count: int = 1,
        file_level: int = logging.INFO,
        fmt: str = "%(asctime)s - %(levelname)s - %(message)s",
        *,
        console_level: int = logging.INFO,
        file_encoding: str = "utf-8",
        force: bool = False,
        delay: bool = True,
        utc: bool = True,
    ) -> logging.Logger:
        """
        Returns a configured logger with time-based rotation.

        Parameters:
        - name: Logger name
        - log_file_path: Path to log file
        - when: Rotation interval (e.g., 'S', 'M', 'H', 'D', 'midnight')
        - interval: How often to rotate (e.g., 1 day if when='midnight')
        - backup_count: Number of backup files to keep
        - file_level: Logging file_level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        - fmt: Log message format
        - console_level: Logging file_level for console handler (default: INFO)
        - file_encoding: Encoding to use when writing the log file (default: utf-8)
        - force: If True, reconfigure logger even if it already has handlers
        - delay: If True, delay file creation until first log write
        - utc: If True, use UTC for rollover times
        """
        if log_file_path is None:
            _current_dir = os.path.dirname(os.path.abspath(__file__))
            log_file_path = os.path.join(_current_dir, '..', '..', 'rs', 'tmp', 'l', 'l')
            try:
                Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

        try:
            Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            output_str = (
                f'ERROR LoggerUtil.get_logger failed: unable to create log directory for {log_file_path}'
            )
            sys.stdout.buffer.write(output_str.encode('utf-8', errors='replace'))

        logger = logging.getLogger(name)
        logger.setLevel(file_level)
        # Avoid propagation to root logger to prevent duplicate messages
        logger.propagate = False

        # Prevent duplicate handlers unless force is requested
        if not logger.handlers or force:
            if force:
                for h in list(logger.handlers):
                    try:
                        logger.removeHandler(h)
                        h.close()
                    except Exception:
                        output_str = (
                            f'ERROR LoggerUtil.get_logger failed: unable to remove handler {h}'
                        )
                        sys.stdout.buffer.write(output_str.encode('utf-8', errors='replace'))

            file_handler = TimedRotatingFileHandler(
                log_file_path,
                when=when,
                interval=interval,
                backupCount=backup_count,
                encoding=file_encoding,
                delay=delay,
                utc=utc,
            )
            formatter = logging.Formatter(fmt)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(file_level)

            console_handler = logging.StreamHandler()
            console_handler.setLevel(console_level)
            console_handler.setFormatter(formatter)

            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger
