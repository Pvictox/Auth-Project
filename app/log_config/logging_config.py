import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "[%(levelname)s] - %(asctime)s - %(filename)s at line %(lineno)d - %(message)s"
DATE_FORMAT = "%d-%m-%Y %H:%M:%S"


class CustomFormatter(logging.Formatter):
    """Formatter customizado com cores para o console"""

    grey = "\x1b[38;21m"
    blue = "\x1b[34;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: grey + LOG_FORMAT + reset,
        logging.INFO: blue + LOG_FORMAT + reset,
        logging.WARNING: yellow + LOG_FORMAT + reset,
        logging.ERROR: red + LOG_FORMAT + reset,
        logging.CRITICAL: bold_red + LOG_FORMAT + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, DATE_FORMAT)
        return formatter.format(record)


class AppOnlyFilter(logging.Filter):
    def filter(self, record):
        # Permitir apenas logs que vêm da pasta 'app'
        return (
            record.pathname.find("/app/") != -1
            or record.pathname.find("\\app\\") != -1
        )


def setup_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(CustomFormatter())
    console_handler.addFilter(AppOnlyFilter())
    root_logger.addHandler(console_handler)

    info_handler = RotatingFileHandler(
        LOG_DIR / "info.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    info_handler.addFilter(lambda record: record.levelno == logging.INFO)
    info_handler.addFilter(AppOnlyFilter())
    root_logger.addHandler(info_handler)

    debug_handler = RotatingFileHandler(
        LOG_DIR / "debug.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    debug_handler.addFilter(lambda record: record.levelno == logging.DEBUG)
    debug_handler.addFilter(AppOnlyFilter())
    root_logger.addHandler(debug_handler)

    error_handler = RotatingFileHandler(
        LOG_DIR / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    error_handler.addFilter(lambda record: record.levelno >= logging.ERROR)
    error_handler.addFilter(AppOnlyFilter())
    root_logger.addHandler(error_handler)

    warning_handler = RotatingFileHandler(
        LOG_DIR / "warning.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    warning_handler.setLevel(logging.WARNING)
    warning_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    warning_handler.addFilter(lambda record: record.levelno == logging.WARNING)
    warning_handler.addFilter(AppOnlyFilter())
    root_logger.addHandler(warning_handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
