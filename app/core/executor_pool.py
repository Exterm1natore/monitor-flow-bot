from typing import Optional
import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
import atexit
from . import environment


# --- Приватные переменные
_executor_instance: Optional[ThreadPoolExecutor] = None
_lock = Lock()


def get_max_workers(default: int = 15) -> int:
    """
    Определяет оптимальное количество потоков на основе CPU и переменных окружения.

    :param default: Значение по умолчанию, если определение не удалось.
    :return: Количество потоков.
    """
    try:
        cpu_limit = int(environment.EXECUTOR_CPU_LIMIT)
        scaling_factor = float(environment.EXECUTOR_SCALING_FACTOR)
        hard_cap = int(environment.EXECUTOR_MAX_HARD_CAP)

        workers = int(cpu_limit * scaling_factor)
        return min(workers, hard_cap)

    except Exception as e:
        logging.getLogger(__name__).warning(
            f"⚠️ Could not determine max_workers: {e}. Using default={default}."
        )
        return default


def get_executor() -> ThreadPoolExecutor:
    """
    Ленивая инициализация глобального ThreadPoolExecutor.

    :return: Глобальный объект исполнителя потока.
    """
    global _executor_instance

    if _executor_instance is None:
        with _lock:
            if _executor_instance is None:
                max_workers = get_max_workers()
                _executor_instance = ThreadPoolExecutor(max_workers=max_workers)
                atexit.register(_shutdown_executor)

    return _executor_instance


def _shutdown_executor():
    """
    Автоматическое завершение пула при завершении приложения.
    """
    global _executor_instance
    if _executor_instance is not None:
        _executor_instance.shutdown(wait=True)
