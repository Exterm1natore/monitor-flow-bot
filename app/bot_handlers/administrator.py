from bot.bot import Bot, Event, EventType
from bot.types import InlineKeyboardMarkup, KeyboardButton
from app.utils import db_records_format
from app import db
from .helpers import (
    catch_and_log_exceptions, administrator_access, send_available_database_tables,
    make_callback_data, parse_callback_data, send_invalid_command_format,
    generate_db_records_page, send_database_table_fields
)
from .constants import (
    Commands, CallbackAction, GET_DATA_REFERENCE, DEL_CHAT_REFERENCE, FIND_DATA_REFERENCE
)
from app.utils import text_format
from app.core import bot_extensions


@catch_and_log_exceptions
@administrator_access
def get_data_command(bot: Bot, event: Event):
    """
    Обработать команду get_data.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    text_items = text_format.normalize_whitespace(event.text).split()
    if not text_items:
        output_text = "⛔️ <b>Команда получения списка из базы данных не распознана.</b>"
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
        )
        return

    # Если нет аргументов в команде
    if len(text_items) == 1:
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, text=GET_DATA_REFERENCE, parse_mode='HTML'
        )
        return

    # Если 1 аргумент в команде
    if len(text_items) == 2:
        if text_items[1] == '-list':
            send_available_database_tables(bot, event.from_chat)
        else:
            # Если введённой таблицы не существует
            if not db.model_exists_by_table_name(text_items[1]):
                not_found_text = "⛔️ <b>Таблицы с таким названием не существует.</b>"
                bot_extensions.send_text_or_raise(
                    bot, event.from_chat, not_found_text, reply_msg_id=event.msgId, parse_mode='HTML'
                )
            else:
                get_data_callback(bot, event, True, table_name=text_items[1])
        return

    # В остальных случаях выводим, что формат команды неверный
    send_invalid_command_format(bot, event.from_chat, Commands.GET_DATA.value, event.msgId)


@catch_and_log_exceptions
@administrator_access
def get_data_callback(bot: Bot, event: Event, is_init: bool = False,
                      *,
                      table_name: str = None):
    """
    Обработать нажатие кнопки для события команды get_data.

    :param bot: VKTeams bot.
    :param event: Событие.
    :param is_init: Флаг, определяющий инициацию обработки.
    (Если установлено True, аргументы, идущие после текущего обязательны).
    :param table_name: Название таблицы получения данных.
    """
    if is_init:
        # Отправляем кнопку с предложением просмотра
        output_text = f"Вы хотите открыть записи указанной таблицы?"
        markup = InlineKeyboardMarkup().row(
            KeyboardButton(
                "Открыть", style="primary", callbackData=make_callback_data(CallbackAction.VIEW_DB, pg=0, tb=table_name)
            )
        )
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, output_text, reply_msg_id=event.msgId, inline_keyboard_markup=markup
        )
        return

    # Если попытка вызвать функцию, где Event не является нажатием кнопки - ошибка
    if event.type != EventType.CALLBACK_QUERY:
        raise TypeError(f"❌ Event is not a type {EventType.CALLBACK_QUERY.value}")

    query_id: str = event.data.get('queryId', None)
    callback: str = event.data.get('callbackData', None)

    if query_id is None or callback is None:
        raise ValueError("❌ queryId or callbackData missing.")

    bot.answer_callback_query(query_id=query_id, text="Request successful.", show_alert=False)

    # Убрать кнопку
    bot_extensions.edit_text_or_raise(
        bot, event.from_chat, event.msgId, "⏳ Ожидайте..."
    )

    # Получает словарь данных кнопки
    try:
        # Если набор параметров данных кнопки не соответствует ожиданиям,
        # считаем, что данные устарели
        cb = parse_callback_data(callback)
        page: int = cb['pg']
        table: str = cb['tb']
    except Exception:
        text = "⛔️ <b>Эта кнопка больше не действует.</b>"
        bot_extensions.edit_text_or_raise(
            bot, event.from_chat, event.msgId, text, inline_keyboard_markup=None
        )
        return

    config = db_records_format.find_config_model_format(table)
    if not config:
        text = f"⛔️ <b>Таблица '{table}' не поддерживается.</b>"
        bot_extensions.edit_text_or_raise(
            bot, event.from_chat, event.msgId, text, parse_mode='HTML'
        )
        return

    model, _, page_size = config
    start = page * page_size + 1
    end = start + page_size - 1

    with db.get_db_session() as session:
        records = db.crud.get_records_range(session, model, start=start, end=end)
        total_records = db.crud.count_records(session, model)

    output_text, markup = generate_db_records_page(records, total_records, config, callback, 'pg')

    bot_extensions.edit_text_or_raise(
        bot, event.from_chat, event.msgId, output_text, inline_keyboard_markup=markup
    )


@catch_and_log_exceptions
@administrator_access
def find_data_command(bot: Bot, event: Event):
    """
    Обработать команду find_data.
    Функция ищет все записи в базе данных, удовлетворяющие заданным фильтрам.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    text_items = text_format.normalize_whitespace(event.text).split()
    if not text_items:
        output_text = "⛔️ <b>Команда поиска по списку базы данных не распознана.</b>"
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
        )
        return

    # Если нет аргументов в команде
    if len(text_items) == 1:
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, text=FIND_DATA_REFERENCE, parse_mode='HTML'
        )
        return

    # Если 1 аргумент в команде
    if len(text_items) == 2:
        if text_items[1] == '-list':
            send_available_database_tables(bot, event.from_chat)
        return

    # Проверяем существование таблицы
    table_name = text_items[1]
    if not db.model_exists_by_table_name(table_name):
        not_found_text = "⛔️ <b>Таблицы с таким названием не существует.</b>"
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, not_found_text, reply_msg_id=event.msgId, parse_mode='HTML'
        )
        return

    # Если 2 аргумента в команде
    if len(text_items) == 3:
        if text_items[2] == '-list':
            send_database_table_fields(bot, event.from_chat, table_name, event.msgId)
            return

    # Если 3 аргумента в команде
    if len(text_items) == 4:
        find_data_callback(bot, event, True,
                           table_name=table_name, field_name=text_items[2], field_value=text_items[3])
        return

    # В остальных случаях выводим, что формат команды неверный
    send_invalid_command_format(bot, event.from_chat, Commands.FIND_DATA.value, event.msgId)


@catch_and_log_exceptions
@administrator_access
def find_data_callback(bot: Bot, event: Event, is_init: bool = False,
                       *,
                       table_name: str = None,
                       field_name: str = None,
                       field_value: str = None):
    """
    Обработать нажатие кнопки для события команды find_data.

    :param bot: VKTeams bot.
    :param event: Событие.
    :param is_init: Флаг, определяющий инициацию обработки.
    (Если установлено True, аргументы, идущие после текущего обязательны).
    :param table_name: Название таблицы поиска.
    :param field_name: Название поля таблицы поиска.
    :param field_value: Название значения поля таблицы поиска.
    """
    if is_init:
        output_text = f"Найти записи по указанным условиям поиска?"
        markup = InlineKeyboardMarkup().row(
            KeyboardButton(
                text='Найти',
                style='primary',
                callbackData=make_callback_data(
                    CallbackAction.FIND_DB, pg=0, tb=table_name, f=field_name, val=field_value
                )
            )
        )
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, output_text, reply_msg_id=event.msgId, inline_keyboard_markup=markup
        )
        return

    # Если попытка вызвать функцию, где Event не является нажатием кнопки - ошибка
    if event.type != EventType.CALLBACK_QUERY:
        raise TypeError(f"❌ Event is not a type {EventType.CALLBACK_QUERY.value}")

    query_id: str = event.data.get('queryId', None)
    callback: str = event.data.get('callbackData', None)

    if query_id is None or callback is None:
        raise ValueError("❌ queryId or callbackData missing.")

    bot.answer_callback_query(query_id=query_id, text="Request successful.", show_alert=False)

    # Убрать кнопку
    bot_extensions.edit_text_or_raise(
        bot, event.from_chat, event.msgId, "⏳ Ожидайте..."
    )

    # Получает словарь данных кнопки
    try:
        # Если набор параметров данных кнопки не соответствует ожиданиям,
        # считаем, что данные устарели
        cb = parse_callback_data(callback)
        page: int = cb['pg']
        table: str = cb['tb']
        field: str = cb['f']
        field_val: str = cb['val']
    except Exception:
        text = "⛔️ <b>Эта кнопка больше не действует.</b>"
        bot_extensions.edit_text_or_raise(
            bot, event.from_chat, event.msgId, text, inline_keyboard_markup=None
        )
        return

    config = db_records_format.find_config_model_format(table)
    if not config:
        text = f"⛔️ <b>Таблица '{table}' не поддерживается.</b>"
        bot_extensions.edit_text_or_raise(
            bot, event.from_chat, event.msgId, text, parse_mode='HTML'
        )
        return

    model, _, _ = config

    try:
        with db.get_db_session() as session:
            records = db.crud.find_records(session, model, field, field_val, partial_match=True)

    except AttributeError:
        error_text = f"⛔️ <b>Некорректный атрибут таблицы '{table}'.</b>"
        bot_extensions.edit_text_or_raise(
            bot, event.from_chat, event.msgId, error_text, parse_mode='HTML'
        )
        return

    output_text, markup = generate_db_records_page(records, len(records), config, callback, 'pg')

    bot_extensions.edit_text_or_raise(
        bot, event.from_chat, event.msgId, output_text, inline_keyboard_markup=markup
    )


@catch_and_log_exceptions
@administrator_access
def del_chat_command(bot: Bot, event: Event):
    """
    Обработать команду del_chat.
    Функция удаляет чат из базы данных, при его наличии.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    text_items = text_format.normalize_whitespace(event.text).split()
    if not text_items:
        output_text = "⛔️ <b>Команда удаления чата не распознана.</b>"
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
        )
        return

    # Если нет аргументов в команде
    if len(text_items) == 1:
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, text=DEL_CHAT_REFERENCE, parse_mode='HTML'
        )
        return

    # Если 1 аргумент в команде
    if len(text_items) == 2:
        with db.get_db_session() as session:
            result = db.crud.delete_chat_by_data(session, text_items[1])

        if result:
            output_text = "✅ <b>Чат успешно удалён из базы данных.</b>"
        else:
            output_text = "⛔️ <b>Чат с таким email не был найден в базе данных.</b>"

        bot_extensions.send_text_or_raise(
            bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
        )
        return

    # В остальных случаях выводим, что формат команды неверный
    send_invalid_command_format(bot, event.from_chat, Commands.DEL_CHAT.value, event.msgId)
