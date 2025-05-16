from typing import List
import time
from concurrent.futures import ThreadPoolExecutor
from bot.bot import Bot


def send_text_to_chats(
        bot: Bot,
        chat_ids: List[str],
        text: str,
        inline_keyboard_markup=None,
        parse_mode=None,
        format_=None,
        max_workers: int = 5,
        wait_for_completion: bool = False
):
    """
    Отправить сообщение в список чатов пользователей.

    :param bot: Объект Bot VKTeams.
    :param chat_ids: Список чатов, в которые отправляется сообщение.
    :param text: Текст сообщения.
    :param inline_keyboard_markup: Встроенная в сообщение клавиатура.
    :param parse_mode: Тип разбора текста.
    :param format_: Описание форматирования текста.
    :param max_workers: Число потоков в пуле.
    :param wait_for_completion: Дождаться завершения всех задач.
    """
    def safe_send(chat_id):
        bot.send_text(
            chat_id=chat_id,
            text=text,
            reply_msg_id=None,
            forward_chat_id=None,
            forward_msg_id=None,
            inline_keyboard_markup=inline_keyboard_markup,
            parse_mode=parse_mode,
            format_=format_
        )

    executor = ThreadPoolExecutor(max_workers=max_workers)
    for i, item_chat_id in enumerate(chat_ids, start=1):
        executor.submit(safe_send, item_chat_id)

    executor.shutdown(wait=wait_for_completion)
