import inspect
from typing import get_type_hints, Optional
from functools import wraps
from bot.bot import Bot, Event
from bot.constant import ChatType
from app import db
from app.core import bot_extensions
import logging
import html
from .constants import (
    INFO_REQUEST_MESSAGE
)


# -------------------- Декораторы --------------------


def catch_and_log_exceptions(func):
    """
    Декоратор для обработки исключений в функции, логирования и отправки ошибок.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except bot_extensions.MessageDeliveryError as delivery_err:
            module = inspect.getmodule(func)
            logger = logging.getLogger(module.__name__ if module else __name__)
            logger.exception(f"Error in {func.__name__}: {str(delivery_err)}")
            return
        except Exception as e:
            module = inspect.getmodule(func)
            logger = logging.getLogger(module.__name__ if module else __name__)
            logger.exception(f"Error in {func.__name__}: {str(e)}")

            # Проверяем, есть ли хотя бы два позиционных аргумента
            bot: Optional[Bot] = None
            event: Optional[Event] = None

            # Проверка в позиционных аргументах
            if len(args) >= 2:
                if isinstance(args[0], Bot) and isinstance(args[1], Event):
                    bot = args[0]
                    event = args[1]

            # Проверка в именованных аргументах
            if 'bot' in kwargs and isinstance(kwargs['bot'], Bot):
                bot = kwargs['bot']
            if 'event' in kwargs and isinstance(kwargs['event'], Event):
                event = kwargs['event']

            # Если оба объекта найдены — отправляем сообщение
            if bot and event:
                exception_text = "❌ <b>Произошла непредвиденная ошибка.</b>"
                bot_extensions.send_text_or_raise(
                    bot=bot,
                    chat_id=event.from_chat,
                    text=exception_text,
                    reply_msg_id=event.msgId,
                    parse_mode='HTML'
                )
            return

    return wrapper


# -------------------- Вспомогательные функции -------


def send_not_found_chat(bot: Bot, chat_id: str, chat_type: str):
    """
    Отправить сообщение, о том, что пользователь или чат не был найден в системе бота.

    :param bot: VKTeams bot.
    :param chat_id: ID чата, в которое направляется сообщение.
    :param chat_type: Тип чата, который не был найден.
    """
    # Если приватный чат
    if chat_type == ChatType.PRIVATE.value:
        not_found_chat_text = ("⚠️ <b>Вас нет в моих списках зарегистрированных пользователей.</b>\n"
                               "Чтобы начать работу, Вы должны быть зарегистрированы в моей системе.\n\n"
                               f"{INFO_REQUEST_MESSAGE}")
    else:
        not_found_chat_text = ("⚠️ <b>Этого чата нет в моих списках зарегистрированных чатов</b>\n"
                               "Чтобы начать работу, чат должен быть добавлен в мои списки.\n\n"
                               f"{INFO_REQUEST_MESSAGE}")

    bot_extensions.send_text_or_raise(
        bot, chat_id, not_found_chat_text, parse_mode='HTML'
    )


def send_notification_types(bot: Bot, chat_id: str):
    """
    Отправить список типов уведомлений в чат.

    :param bot: VKTeams bot.
    :param chat_id: Чат, в который отправляется список.
    """
    with db.get_db_session() as session:
        types = db.crud.get_all_records(session, db.NotificationType)
        names = [t.type for t in types]

    output_text = ("<b>Список всех типов уведомлений:</b>\n"
                   f"[{html.escape(', '.join(names))}]")

    bot_extensions.send_long_text(
        bot, chat_id, output_text, parse_mode='HTML'
    )


def send_notification_types_access(bot: Bot, chat_id: str, to_subscribe: bool):
    """
    Отправить список доступных типов уведомлений для подписки/отписки.

    :param bot: VKTeams bot.
    :param chat_id: Чат, в который отправляется список.
    :param to_subscribe: Формировать список по условию есть/нет подписки.
    """
    with db.get_db_session() as session:
        chat = db.crud.find_chat(session, chat_id)

        # Если для подписки
        if to_subscribe:
            if chat is None:
                types = db.crud.get_all_records(session, db.NotificationType)
            else:
                types = db.crud.find_unsubscribed_notification_types(session, chat)

            names = [t.type for t in types]
            output_text = ("<b>Список типов уведомлений, на которые нет подписки:</b>\n"
                           f"{'[' + html.escape(', '.join(names)) + ']' if names else 'Нет доступных.'}")
        else:
            if chat is None:
                output_text = ("⚠️ <b>Вы не зарегистрированы.</b>\n"
                               "У вас нет ни одной подписки на уведомления.")
            else:
                names = [
                    ns.notification_type_model.type
                    for ns in chat.notification_subscribers
                ]
                output_text = ("<b>Список типов уведомлений, на которые есть подписка:</b>\n"
                               f"{'[' + html.escape(', '.join(names)) + ']' if names else 'Нет доступных'}")

    bot_extensions.send_long_text(
        bot, chat_id, output_text, parse_mode='HTML'
    )


def send_notification_description(bot: Bot, chat_id: str, type_name: str):
    """
    Отправить описание заданного типа уведомления в чат.

    :param bot: VKTeams bot.
    :param chat_id: Чат, в который отправляется список.
    :param type_name: Имя типа уведомления.
    """
    with db.get_db_session() as session:
        notification_type = db.crud.find_notification_type(session, type_name)

    if not notification_type:
        output_text = f"⚠️ <b>Тип уведомления '<i>{html.escape(type_name)}</i>' не существует.</b>"
    else:
        output_text = (f"<b>Тип уведомления '<i>{html.escape(type_name)}</i>'</b>\n"
                       f"Описание:\n\"{html.escape(notification_type.description)}\"")

    bot_extensions.send_long_text(
        bot, chat_id, output_text, parse_mode='HTML'
    )
