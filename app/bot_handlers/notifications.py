from typing import List, Optional
import logging
from bot.bot import Bot
from .constants import NotificationTypes
from app.core import bot_extensions
from app import db


def send_notification_to_subscribers(bot: Bot, notification_type: NotificationTypes, text: str,
                                     inline_keyboard_markup=None, parse_mode: str = None, format_=None,
                                     logger: Optional[logging.Logger] = None):
    """
    Отправить уведомление в чаты, подписанные за данный тип уведомлений.

    :param bot: VKTeams bot.
    :param notification_type: Тип уведомления.
    :param text: Текст уведомления.
    :param inline_keyboard_markup: Встроенная в сообщение клавиатура.
    :param parse_mode: Тип разбора текста.
    :param format_: Описание форматирования текста (передаётся раздельно с parse_mod).
    :param logger: Внешний логгер.
    """
    with db.get_db_session() as session:
        notify_type = db.crud.find_notification_type(session, notification_type.value)

        if notify_type is None:
            raise ValueError(f"Notification type '{notification_type.value}' does not exist in the database.")

        subscribers: List[db.NotificationSubscriber] = notify_type.subscribers.all()

        # Получаем список email чатов, для отправки
        emails = [
            subscriber.chat.email
            for subscriber in subscribers
        ]

    # Если есть хотя-бы один подписчик отправляем уведомление
    if emails:
        notify_text = f"🔔 Новое уведомление.\n\n{text}"
        bot_extensions.broadcast_to_chats(
            bot=bot,
            chat_ids=emails,
            text=notify_text,
            inline_keyboard_markup=inline_keyboard_markup,
            parse_mode=parse_mode,
            format_=format_,
            wait_for_completion=False,
            logger=logger,
            suppress_notification_log=False,
        )


def send_notification_to_administrators(bot: Bot, text: str, inline_keyboard_markup=None,
                                        parse_mode: str = None, format_=None):
    """
    Отправить оповещение для всех администраторов.

    :param bot: VKTeams bot.
    :param text: Текст уведомления.
    :param inline_keyboard_markup: Встроенная в сообщение клавиатура.
    :param parse_mode: Тип разбора текста.
    :param format_: Описание форматирования текста.
    """
    with db.get_db_session() as session:
        administrators = db.crud.get_all_records(session, db.Administrator)

        # Получаем список email чатов, для отправки
        emails = [
            admin.user.chat.email
            for admin in administrators
        ]

    # Если есть хотя бы один администратор
    if emails:
        notify_text = f"📫 Оповещение системы.\n\n{text}"
        bot_extensions.broadcast_to_chats(
            bot=bot,
            chat_ids=emails,
            text=notify_text,
            inline_keyboard_markup=inline_keyboard_markup,
            parse_mode=parse_mode,
            format_=format_,
            wait_for_completion=False,
            logger=None,
            suppress_notification_log=False,
        )
