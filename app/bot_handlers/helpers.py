import inspect
import json
from typing import get_type_hints, Optional, List, Any, Dict
from functools import wraps
from bot.bot import Bot, Event
from bot.constant import ChatType
from app import db
from .constants import (
    CallbackAction
)
from app.core import bot_extensions
import logging
import html
from .constants import (
    INFO_REQUEST_MESSAGE
)


# -------------------- Декораторы --------------------


def administrator_access(func):
    """
    Проверить и выполнить функцию только в случае, если определён доступ администратора.
    """
    sig = inspect.signature(func)
    params = list(sig.parameters.values())

    if len(params) < 2:
        raise TypeError(f"❌ The function '{func.__name__}' must take at least two arguments: Bot and Event.")

    # Получаем аннотации типов
    type_hints = get_type_hints(func)

    first_param_type = type_hints.get(params[0].name)
    second_param_type = type_hints.get(params[1].name)

    # Проверяем соответствие типам
    if first_param_type is not Bot or second_param_type is not Event:
        raise TypeError(
            f"❌ The first two parameters of the function '{func.__name__}' must have types Bot and Event respectively.\n"
            f"Detected: {first_param_type} and {second_param_type}"
        )

    @wraps(func)
    def wrapper(bot: Bot, event: Event, *args, **kwargs):
        try:
            # Если приватный тип чата
            if event.chat_type == ChatType.PRIVATE.value:
                with db.get_db_session() as session:
                    chat = db.crud.find_chat(session, event.from_chat)
                    user = chat.user if chat is not None else None
                    is_admin = db.crud.is_user_administrator(session, user) \
                        if user is not None else False

                # Если чат не существует или пользователь не является администратором
                if chat is None or user is None or not is_admin:
                    raise PermissionError("⛔️ <b>Нет доступа для выполнения команды.</b>\n"
                                          "Вы не администратор.")
            else:
                response = bot.get_chat_admins(event.from_chat)
                response.raise_for_status()

                response_data = response.json()

                # Если ответ за запрос списка администраторов корректен
                if response_data.get('ok', False):
                    is_admin = any(user['userId'] == event.message_author['userId'] for user in response_data.get('admins', []))
                    'admins'
                    if not is_admin:
                        raise PermissionError("⛔️ <b>Нет доступа для выполнения команды.</b>\n"
                                              "Вы не администратор группы.")
                else:
                    error_text = "❌ <b>Нет возможности выполнить команду.</b>"

                    desc_error: str = response_data.get('description', "")

                    if "permission denied" in desc_error.lower():
                        error_text += ("\nБот не обладает правами администратора данной группы, "
                                       "для выполнения заданного действия.")
                    else:
                        error_text += f"\nПричина: {desc_error}"

                    raise PermissionError(error_text)
        except PermissionError as permission_error:
            bot_extensions.send_text_or_raise(
                bot, event.from_chat, str(permission_error), reply_msg_id=event.msgId, parse_mode='HTML'
            )
            return
        except Exception as other_error:
            error_text = "❌ <b>Нет возможности выполнить команду.</b>"
            error_text += f"\nПричина: {str(other_error)}"
            logging.getLogger(__name__).exception(other_error)

            bot_extensions.send_text_or_raise(
                bot, event.from_chat, error_text, reply_msg_id=event.msgId, parse_mode='HTML'
            )
            return

        return func(bot, event, *args, **kwargs)

    return wrapper


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


def send_available_database_tables(bot: Bot, chat_id: str):
    """
    Отправить список доступных таблиц базы данных.

    :param bot: VKTeams bot.
    :param chat_id: Чат, в который отправляется список.
    """
    tables: List[str] = list(db.models.Base.metadata.tables.keys())

    output_text = ("<b>Список доступных таблиц базы данных:</b>\n"
                   f"{'[' + html.escape(', '.join(tables)) + ']' if tables else 'Нет доступных'}")

    bot_extensions.send_long_text(
        bot, chat_id, output_text, parse_mode='HTML'
    )


def make_callback_data(action: CallbackAction, **params) -> str:
    """Генерирует callback_data в JSON-формате."""
    payload = {"action": action.value}
    payload.update(params)
    return json.dumps(payload, separators=(',', ':'))


def parse_callback_data(data: str) -> Dict[str, Any]:
    """Преобразует JSON-строку в словарь с проверкой."""
    try:
        parsed = json.loads(data)
        if "action" not in parsed:
            raise ValueError("Missing 'action' in callback_data.")
        return parsed
    except json.JSONDecodeError:
        raise ValueError("Invalid callback_data format.")
