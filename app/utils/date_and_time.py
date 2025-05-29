from typing import Optional, Union
from datetime import datetime
from dateutil import parser
import pytz


def get_current_date_moscow() -> datetime:
    """
    Получить текущую дату по Москве.

    :return: Текущая дата в виде datetime
    """
    now = datetime.now()

    # Определяем нужный часовой пояс
    desired_timezone = pytz.timezone('Europe/Moscow')

    # Переводим текущую дату и время в нужный часовой пояс
    now_in_desired_timezone = now.astimezone(desired_timezone)

    return now_in_desired_timezone


def get_current_date_with_format(format_date: str = "%d.%m.%Y %H:%M") -> str:
    """
    Получить текущую дату по Москве в виде форматированной строки в заданном формате.

    :param format_date: Формат даты в виде строки (по стандарту "%d.%m.%Y %H:%M")
    :return: Текущая дата в виде строки в заданном формате
    """
    # Ожидаем асинхронный вызов для получения текущей даты в часовом поясе Москвы
    now_in_desired_timezone = get_current_date_moscow()

    # Форматируем дату в заданном формате
    formatted_time = now_in_desired_timezone.strftime(format_date)

    return formatted_time


def format_datetime(
    dt: Optional[Union[datetime, str, int]] = None,
    *,
    tz: str = "Europe/Moscow",
    fmt: str = "%Y-%m-%d %H:%M:%S",
    to_local: bool = False,
    parse_string: bool = True
) -> str:
    """
    Форматировать дату/время в формат строки.

    :param dt:
        - datetime — форматируется напрямую;
        - str — если parse_string=True, будет распарсена через dateutil.parser;
        - int — Unix-timestamp (секунды);
        - None — берётся текущее время UTC.
    :param tz: Часовой пояс, в который переводить результат (pytz timezone name).
    :param fmt: Шаблон strftime для вывода.
    :param to_local:
        - True — сначала локализует/переведёт dt в указанный tz;
        - False — оставит dt «как есть» (полезно, если уже локальное).
    :param parse_string: Если dt — str, попытаться распарсить. Иначе ошибка.
    :return: Отформатированная строка даты/времени.
    :raises ValueError: Если строка не может быть распознана или tz некорректен.
    """
    # 1. Получаем объект datetime
    if dt is None:
        # текущее время UTC
        dt_obj = datetime.utcnow().replace(tzinfo=pytz.UTC)
    elif isinstance(dt, datetime):
        dt_obj = dt if dt.tzinfo else dt.replace(tzinfo=pytz.UTC)
    elif isinstance(dt, (int, float)):
        # Unix timestamp
        dt_obj = datetime.fromtimestamp(dt, tz=pytz.UTC)
    elif isinstance(dt, str):
        if not parse_string:
            raise ValueError("Received string datetime but parse_string=False")
        try:
            dt_obj = parser.parse(dt)
            if not dt_obj.tzinfo:
                dt_obj = dt_obj.replace(tzinfo=pytz.UTC)
        except (ValueError, OverflowError) as e:
            raise ValueError(f"Cannot parse datetime string: {dt}") from e
    else:
        raise TypeError(f"Unsupported type for dt: {type(dt)}")

    # 2. Переводим в указанный timezone
    if to_local:
        try:
            target_tz = pytz.timezone(tz)
        except pytz.UnknownTimeZoneError as e:
            raise ValueError(f"Unknown timezone: {tz}") from e
        dt_obj = dt_obj.astimezone(target_tz)

    # 3. Форматируем
    return dt_obj.strftime(fmt)
