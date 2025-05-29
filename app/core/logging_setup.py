import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from bot.bot import Bot
from . import environment
from app.bot_handlers import notifications, constants


# --- Основной конфиг
LOG_DIRECTORY = Path(environment.LOG_DIRECTORY)
LOG_FILENAME = "app.log"
MAX_LOG_SIZE = 2 * 1024 * 1024
BACKUP_COUNT = 5


class BotChatLoggingHandler(logging.Handler):
    """
    Logging-Handler, делающий рассылку подписчикам уведомлений.
    """
    def __init__(self, bot: Bot, level=logging.ERROR):
        super().__init__(level)
        self.bot = bot
        self._internal_logger = logging.getLogger(__name__)

    def emit(self, record: logging.LogRecord):
        try:
            # Чтобы избежать бесконечной рекурсии, не пересылаем сообщения от самого этого логгера
            if record.name == __name__:
                return

            msg = self.format(record)
            notifications.send_notification_to_subscribers(
                self.bot, constants.NotificationTypes.SYSTEM, msg, logger=self._internal_logger
            )

        except Exception as e:
            self._internal_logger.exception(f"Error sending logs to subscribers: {str(e)}")


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

    from app.core.bot_setup import app
    notify_handler = BotChatLoggingHandler(app, level=logging.ERROR)
    notify_handler.setFormatter(formatter)
    root_logger.addHandler(notify_handler)

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
