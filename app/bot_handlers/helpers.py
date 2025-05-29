import inspect
import json
import logging
import html
from typing import get_type_hints, Optional, List, Any, Dict, Tuple
from functools import wraps
from bot.bot import Bot, Event, EventType
from bot.constant import ChatType
from bot.types import InlineKeyboardMarkup, KeyboardButton
from app import db
from .constants import (
    CallbackAction, INFO_REQUEST_MESSAGE
)
from app.core import bot_extensions
from app.utils import db_records_format


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
                    is_admin = user.administrator is not None \
                        if user is not None else False

                # Если чат не существует или пользователь не является администратором
                if chat is None or user is None or not is_admin:
                    raise PermissionError("⛔️ Нет доступа для выполнения команды.\n"
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
                        raise PermissionError("⛔️ Нет доступа для выполнения команды.\n"
                                              "Вы не администратор группы.")
                else:
                    error_text = "❌ Нет возможности выполнить команду."

                    desc_error: str = response_data.get('description', "")

                    if "permission denied" in desc_error.lower():
                        error_text += ("\nБот не обладает правами администратора данной группы, "
                                       "для выполнения заданного действия.")
                    else:
                        error_text += f"\nПричина: {desc_error}"

                    raise PermissionError(error_text)
        except PermissionError as permission_error:
            # Если кнопка и приватный чат
            if event.type == EventType.CALLBACK_QUERY and event.chat_type == ChatType.PRIVATE.value:
                bot.answer_callback_query(query_id=event.queryId, text="Request successful", show_alert=False)
                bot_extensions.edit_text_or_raise(
                    bot, event.from_chat, event.msgId, event.data['message'].get('text', "Скрыто..."),
                    inline_keyboard_markup=None
                )
            bot_extensions.send_text_or_raise(
                bot, event.from_chat, str(permission_error), reply_msg_id=event.msgId, parse_mode='HTML'
            )
            return
        except Exception as other_error:
            error_text = "❌ Нет возможности выполнить команду."
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
                exception_text = "❌ Произошла непредвиденная ошибка."
                # Если кнопка
                if event.type == EventType.CALLBACK_QUERY:
                    try:
                        bot_extensions.edit_text_or_raise(
                            bot=bot,
                            chat_id=event.from_chat,
                            msg_id=event.msgId,
                            text=exception_text,
                            inline_keyboard_markup=None
                        )
                        return
                    except Exception as edit_text_error:
                        error_text = ("❌ An error occurred while handling an exception and attempting to edit the message: "
                                      f"{str(edit_text_error)}")
                        logging.getLogger(__name__).error(error_text)

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
        not_found_chat_text = ("⚠️ Вас нет в моих списках зарегистрированных пользователей.\n"
                               "Чтобы начать работу, Вы должны быть зарегистрированы в моей системе.\n\n"
                               f"{INFO_REQUEST_MESSAGE}")
    else:
        not_found_chat_text = ("⚠️ Этого чата нет в моих списках зарегистрированных чатов.\n"
                               "Чтобы начать работу, чат должен быть добавлен в мои списки.\n\n"
                               f"{INFO_REQUEST_MESSAGE}")

    bot_extensions.send_text_or_raise(
        bot, chat_id, not_found_chat_text, parse_mode='HTML'
    )


def send_invalid_command_format(bot: Bot, chat_id: str, command: str, msg_id: int = None):
    """
    Отправить сообщение, сообщающее о некорректном формате команды.

    :param bot: VKTeams bot.
    :param chat_id: ID чата, в которое направляется сообщение.
    :param command: Название команды (без символа '/').
    :param msg_id: ID сообщения, на которое отправляется ответ (опционально).
    """
    output_text = ("⛔️ Некорректный формат команды.\n"
                   f"Чтобы узнать какой формат необходим, отправьте мне /{command} ")
    bot_extensions.send_text_or_raise(
        bot, chat_id, output_text, reply_msg_id=msg_id, parse_mode='HTML'
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

        output_text = ("<b>Список всех типов уведомлений:</b>\n\n"
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
            output_text = ("<b>Список типов уведомлений, на которые нет подписки:</b>\n\n"
                           f"{'[' + html.escape(', '.join(names)) + ']' if names else 'Нет доступных.'}")
        else:
            if chat is None:
                output_text = ("⚠️ Вы не зарегистрированы.\n"
                               "У вас нет ни одной подписки на уведомления.")
            else:
                names = [
                    ns.notification_type_model.type
                    for ns in chat.notification_subscribers
                ]
                output_text = ("<b>Список типов уведомлений, на которые есть подписка:</b>\n\n"
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
            output_text = f"⚠️ Тип уведомления '<i>{html.escape(type_name)}</i>' не существует."
        else:
            output_text = (f"Тип уведомления '<i>{html.escape(type_name)}</i>'.\n\n"
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

    output_text = ("<b>Список доступных таблиц базы данных:</b>\n\n"
                   f"{'[' + html.escape(', '.join(tables)) + ']' if tables else 'Нет доступных'}")

    bot_extensions.send_long_text(
        bot, chat_id, output_text, parse_mode='HTML'
    )


def send_database_table_fields(bot: Bot, chat_id: str, table_name: str, reply_msd_id: Optional[str]):
    """
    Отправить список полей заданной таблицы (название - тип).
    В случае, если таблица не была найдена, вместо списка полей, выводится её отсутствие.

    :param bot: VKTeams bot.
    :param chat_id: Чат, в который отправляется список.
    :param table_name: Название таблицы базы данных.
    :param reply_msd_id: Ответить на сообщение с заданным ID, если таблица не найдена.
    """
    if not db.model_exists_by_table_name(table_name):
        not_found_text = "⛔️ Таблицы с таким названием не существует."
        bot_extensions.send_text_or_raise(
            bot, chat_id, not_found_text, reply_msg_id=reply_msd_id, parse_mode='HTML'
        )
        return
    cols_info = []
    for col in db.get_table_columns(table_name):
        cols_info.append(f"{col.name} — {col.type}")
    text = (
            f"Поля таблицы '{table_name}':\n\n" +
            "\n".join(line for line in cols_info)
    )
    bot_extensions.send_text_or_raise(
        bot, chat_id, text
    )


def make_callback_data(action: CallbackAction, **params) -> str:
    """
    Генерирует callback_data в JSON-формате.

    :param action: Действие для callback_data.
    :param params: Дополнительные параметры callback_data.
    """
    payload = {"action": action.value}
    payload.update(params)
    return json.dumps(payload, separators=(',', ':'))


def validate_and_make_callback_data(data: dict) -> str:
    """
    Проверяет словарь и возвращает callback_data строку.

    :param data: Словарь, содержащий 'action' и дополнительные параметры.
    :return: JSON-строка callback_data.
    :raises ValueError: Отсутствие ключа 'action' или он некорректен.
    """
    if "action" not in data:
        raise ValueError("Missing 'action' in data")

    action_value = data["action"]

    if not CallbackAction.is_valid(action_value):
        raise ValueError(f"Invalid action value: {action_value}")

    action_enum = CallbackAction(action_value)

    # Удаляем action из словаря и передаём остальные параметры
    params = {k: v for k, v in data.items() if k != "action"}
    return make_callback_data(action_enum, **params)


def parse_callback_data(data: str) -> Dict[str, Any]:
    """
    Преобразует JSON-строку в словарь с проверкой.

    :param data: Строка, содержащая callback_data в формате json.
    :return: Преобразованный словарь.
    :raise ValueError: Отсутствие ключа 'action';
                       Некорректный формат callback_data.
    """
    try:
        parsed = json.loads(data)
        if "action" not in parsed:
            raise ValueError("Missing 'action' in callback_data.")
        return parsed
    except json.JSONDecodeError:
        raise ValueError("Invalid callback_data format.")


def generate_db_records_page(records: List[db.T], total_records: int,
                             model_config: db_records_format.ModelFormatConfig,
                             callback_data: str, page_key: str) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
    """
    Сформировать и отформатировать данные для страничного вывода записей базы данных в чат.

    :param records: Список ORM-моделей записей базы данных.
    :param total_records: Максимальное количество записей всей выборки (используется для добавления кнопки 'Далее').
    :param model_config: Конфигурация модели для полученного списка записей.
    :param callback_data: Полученные данные вызова кнопки чата.
    :param page_key: Ключ значения страницы в данных вызова кнопки.
    :return: Кортеж, состоящий из текста и опциональной встроенной клавиатуры.
    """
    model, model_fields, page_size = model_config
    table_name = db.get_tablename_by_model(model)
    callback_dict = parse_callback_data(callback_data)
    page: int = callback_dict[page_key]

    # Последняя ли страница
    has_next = page * page_size + page_size < total_records

    # Кнопки перехода
    markup: Optional[InlineKeyboardMarkup] = None
    button_back: Optional[KeyboardButton] = None
    button_next: Optional[KeyboardButton] = None

    if page > 0:
        # Обновляем параметры номер страницы
        back_callback_dict = callback_dict.copy()
        back_callback_dict[page_key] = page - 1
        back_callback_data = validate_and_make_callback_data(back_callback_dict)

        button_back = KeyboardButton(
            text='<< Назад', style='primary', callbackData=back_callback_data
        )

    if has_next:
        # Обновляем параметры номер страницы
        next_callback_dict = callback_dict.copy()
        next_callback_dict[page_key] = page + 1
        next_callback_data = validate_and_make_callback_data(next_callback_dict)

        button_next = KeyboardButton(
            text='Дальше >>', style='primary', callbackData=next_callback_data
        )

    # Формируем разметку кнопок
    if button_back is not None or button_next is not None:
        markup = InlineKeyboardMarkup()
        row = []
        if button_back is not None:
            row.append(button_back)
        if button_next is not None:
            row.append(button_next)
        markup.row(*row)

    if not records:
        text = f"Список найденных записей таблицы '{table_name}'\n\n📭 Записей нет."
        return text, markup

    format_records = db_records_format.format_for_chat(records, model_fields=model_fields)
    text = f"Список найденных записей таблицы '{table_name}'\n\n{format_records}"
    return text, markup
