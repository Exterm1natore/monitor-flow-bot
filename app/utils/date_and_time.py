from datetime import datetime
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
