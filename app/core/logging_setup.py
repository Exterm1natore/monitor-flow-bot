import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from . import environment

# --- Основной конфиг
LOG_DIRECTORY = Path(environment.LOG_DIRECTORY)
LOG_FILENAME = "app.log"
MAX_LOG_SIZE = 2 * 1024 * 1024
BACKUP_COUNT = 5


def enable_logging(level: str = "INFO"):
    """
    Включает централизованное логирование для всего проекта.

    :param level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIRECTORY / LOG_FILENAME

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # --- Консольный хендлер с traceback ---
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # --- Файловый хендлер с ротацией
    file_handler = RotatingFileHandler(
        filename=log_path,
        maxBytes=MAX_LOG_SIZE,
        backupCount=BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # --- Настройка root-логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Подавляем лишний шум
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Устанавливаем глобальный перехватчик исключений
    sys.excepthook = _handle_exception


def _handle_exception(exc_type, exc_value, exc_traceback):
    """
    Глобальный перехватчик исключений для логирования ошибок, не пойманных вручную.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.getLogger().critical(
        "Unprocessed Exception:",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
