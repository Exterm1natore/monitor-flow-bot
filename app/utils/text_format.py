from typing import List
import re


def split_text(text: str, max_length: int) -> List[str]:
    """
    Функция для деления текста на несколько частей, каждая из которых не превышает max_length.

    :param text: Входной текст, который нужно разделить.
    :param max_length: Максимальная длина одной части текста.
    :return: Список строк, каждая из которых не превышает max_length.
    """
    # Список для хранения частей текста
    parts = []

    # Пока длина текста больше максимальной длины, разделяем его
    while len(text) > max_length:
        # Разбиваем текст на части
        part = text[:max_length]
        parts.append(part)
        text = text[max_length:]  # Оставшийся текст для следующей итерации

    # Добавляем оставшийся текст, если он есть
    if text:
        parts.append(text)

    return parts


def normalize_whitespace(text: str) -> str:
    """
    Удаляет все лишние пробельные символы (в начале и конце, а также дублирующиеся).

    :param text: Входящий текст.
    :return: Форматированный текст.
    """
    return ' '.join(re.split(r'\s+', text.strip()))
