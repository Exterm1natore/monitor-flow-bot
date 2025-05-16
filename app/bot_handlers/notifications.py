from typing import List
from bot.bot import Bot
from .constants import NotificationTypes
from app.core import bot_extensions
from app import db


def send_notification_to_subscribers(bot: Bot, notification_type: NotificationTypes, text: str,
                                     parse_mode: str = None):
    """
    Отправить уведомление определённого типа всем подписчикам.

    :param bot: VKTeams bot.
    :param notification_type: Тип уведомления.
    :param text: Текст уведомления.
    :param parse_mode: Тип разбора текста.
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
        bot_extensions.send_text_to_chats(bot, emails, notify_text, parse_mode=parse_mode)
