from pathlib import Path
from dotenv import load_dotenv
import os


def load_environment():
    """
    Загружает переменные окружения из .env файла.
    1. Если файл .env есть в корне проекта, ищем переменную ENV_PATH.
    2. Если ENV_PATH задан, загружаем переменные из указанного пути.
    3. Если ENV_PATH не задан, загружаем переменные из .env корня проекта.
    4. Если .env не найден, выбрасывается исключение.

    :raise FileNotFoundError: Файл .env не был найден в корне проекта.
    """
    # Проверяем наличие файла .env в корне проекта
    env_file = Path('.') / '.env'
    if env_file.exists():
        # Если переменная окружения ENV_PATH задана, загружаем из указанного пути
        env_path = os.getenv("ENV_PATH")
        if env_path and Path(env_path).exists():
            load_dotenv(dotenv_path=env_path)
            # print(f"✅ Loaded .env from custom path: {env_path}")
        else:
            # Если ENV_PATH не задан, загружаем из .env в корне проекта
            load_dotenv(dotenv_path=env_file)
            # print(f"✅ Loaded .env from: {env_file}")
    else:
        # Если .env не найден в корне проекта, выбрасываем исключение
        raise FileNotFoundError("❌ .env file not found in the root project directory.")


# Загружаем переменные окружения
load_environment()


# --------------------------------------- Путь к директории логов ----------------------------------

LOG_DIRECTORY = os.environ["LOG_DIRECTORY"]

# --------------------------------------------------------------------------------------------------

# --------------------------------------- Токен VKTeams бота ---------------------------------------

BOT_TOKEN = os.environ["VKTEAMS_BOT_TOKEN"]

# --------------------------------------------------------------------------------------------------

# --------------------------------------- Путь к базе данных ---------------------------------------

DB_PATH = os.environ["DB_PATH"]

# --------------------------------------------------------------------------------------------------

# --------------------------------------- Данные запуска uvicorn сервера FastAPI -------------------

WEBHOOK_EVENT_ENDPOINT = os.environ["WEBHOOK_EVENT_ENDPOINT"]

API_HOST = os.environ["API_HOST"]

API_PORT = int(os.environ["API_PORT"])

# --------------------------------------------------------------------------------------------------

# --------------------------------------- Данные для работы с потоками -----------------------------

EXECUTOR_CPU_LIMIT = os.environ["EXECUTOR_CPU_LIMIT"]
EXECUTOR_SCALING_FACTOR = os.environ["EXECUTOR_SCALING_FACTOR"]
EXECUTOR_MAX_HARD_CAP = os.environ["EXECUTOR_MAX_HARD_CAP"]

# --------------------------------------------------------------------------------------------------
