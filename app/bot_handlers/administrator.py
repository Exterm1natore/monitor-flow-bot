from typing import Optional
import html
from bot.bot import Bot, Event, EventType
from bot.constant import ChatType
from bot.types import InlineKeyboardMarkup, KeyboardButton
from app.utils import db_records_format, date_and_time
from app import db
from .helpers import (
    catch_and_log_exceptions, administrator_access, send_available_database_tables,
    make_callback_data, parse_callback_data, send_invalid_command_format,
    generate_db_records_page, send_database_table_fields, send_notification_types,
    send_notification_description
)
from .constants import (
    Commands, CallbackAction, GET_DATA_REFERENCE, DEL_CHAT_REFERENCE, FIND_DATA_REFERENCE,
    ADD_NOTIFY_SUBSCRIBER_REFERENCE, DEL_NOTIFY_SUBSCRIBER_REFERENCE, ADD_ADMIN_REFERENCE,
    DEL_ADMIN_REFERENCE
)
from app.utils import text_format
from app.core import bot_extensions
from app.bot_handlers import notifications


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
        output_text = "⛔️ Команда получения списка из базы данных не распознана."
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
            return
        else:
            # Если введённой таблицы не существует
            if not db.model_exists_by_table_name(text_items[1]):
                not_found_text = "⛔️ Таблицы с таким названием не существует."
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
        text = "⛔️ Эта кнопка больше не действует."
        bot_extensions.edit_text_or_raise(
            bot, event.from_chat, event.msgId, text, inline_keyboard_markup=None
        )
        return

    config = db_records_format.find_config_model_format(table)
    if not config:
        text = f"⛔️ Таблица '{table}' не поддерживается."
        bot_extensions.edit_text_or_raise(
            bot, event.from_chat, event.msgId, text
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
        output_text = "⛔️ Команда поиска по списку базы данных не распознана."
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
        not_found_text = "⛔️ Таблицы с таким названием не существует."
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
        text = "⛔️ Эта кнопка больше не действует."
        bot_extensions.edit_text_or_raise(
            bot, event.from_chat, event.msgId, text, inline_keyboard_markup=None
        )
        return

    config = db_records_format.find_config_model_format(table)
    if not config:
        text = f"⛔️ Таблица '{table}' не поддерживается."
        bot_extensions.edit_text_or_raise(
            bot, event.from_chat, event.msgId, text, parse_mode='HTML'
        )
        return

    model, _, _ = config

    try:
        with db.get_db_session() as session:
            records = db.crud.find_records(session, model, {field: field_val}, partial_match=True)
            output_text, markup = generate_db_records_page(records, len(records), config, callback, 'pg')

    except AttributeError:
        error_text = f"⛔️ Некорректный атрибут таблицы '{table}'."
        bot_extensions.edit_text_or_raise(
            bot, event.from_chat, event.msgId, error_text, parse_mode='HTML'
        )
        return

    bot_extensions.edit_text_or_raise(
        bot, event.from_chat, event.msgId, output_text, inline_keyboard_markup=markup
    )


@catch_and_log_exceptions
@administrator_access
def add_notify_subscriber_command(bot: Bot, event: Event):
    """
    Обработать команду add_notify_subscriber.
    Функция добавляет нового подписчика заданного типа уведомлений.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    text_items = text_format.normalize_whitespace(event.text).split()
    if not text_items:
        output_text = "⛔️ Команда подписки чата на уведомления не распознана."
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
        )
        return

    # Если нет аргументов в команде
    if len(text_items) == 1:
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, text=ADD_NOTIFY_SUBSCRIBER_REFERENCE, parse_mode='HTML'
        )
        return

    # Если 1 аргумент в команде
    if len(text_items) == 2:
        if text_items[1] == '-list':
            send_notification_types(bot, event.from_chat)
            return

    # Если 2 аргумента в команде
    if len(text_items) == 3:
        if text_items[2] == '-desc':
            send_notification_description(bot, event.from_chat, text_items[1])
            return
        else:
            with db.get_db_session() as session:
                chat = db.crud.find_chat(session, text_items[1])
                notify_type = db.crud.find_notification_type(session, text_items[2])
                subscriber: Optional[db.NotificationSubscriber] = db.crud.find_one_record(
                    session,
                    db.NotificationSubscriber,
                    {
                        db.NotificationSubscriber.chat_id: chat.id,
                        db.NotificationSubscriber.notification_type: notify_type.id
                    }
                ) if chat is not None and notify_type is not None else None

                is_correct = False
                if chat is None:
                    output_text = "⛔️ Чат с таким email не был найден в базе данных.\n"
                elif notify_type is None:
                    output_text = "⛔️ Такой тип уведомлений не был найден в базе данных.\n"
                elif subscriber:
                    output_text = "✅ Чат уже подписан на выбранный тип уведомлений.\n"
                else:
                    db.crud.add_notification_subscriber(
                        session, chat, notify_type, event.from_chat, date_and_time.get_current_date_moscow()
                    )
                    output_text = (f"✅ Чат c email = '<i>{html.escape(chat.email)}</i>' "
                                   f"успешно подписан уведомления типа '<i>{html.escape(notify_type.type)}</i>'.\n")
                    is_correct = True
                    chat_email = chat.email
                    notify_type_type = notify_type.type

            # Направляем результат в текущий чат
            bot_extensions.send_text_or_raise(
                bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
            )

            if is_correct:
                # Сообщить администраторам о новом подписчике на уведомления
                admin_notify_text = (f"Чат с email = '{chat_email}' был подписан на уведомления типа '{notify_type_type}' "
                                     f"(пользователем: {html.escape(event.from_chat)}).")
                notifications.send_notification_to_administrators(bot, admin_notify_text)

                # Сообщить в подписавшийся чат о подписке
                bot_extensions.send_text_or_raise(
                    bot, chat_email, f"📩 Система: Вы подписаны на уведомления типа "
                                     f"'<i>{html.escape(notify_type_type)}</i>'",
                    parse_mode='HTML'
                )
            return

    # В остальных случаях выводим, что формат команды неверный
    send_invalid_command_format(bot, event.from_chat, Commands.ADD_NOTIFY_SUBSCRIBER.value, event.msgId)


@catch_and_log_exceptions
@administrator_access
def del_notify_subscriber_command(bot: Bot, event: Event):
    """
    Обработать команду del_notify_subscriber.
    Функция удаляет подписчика заданного типа уведомлений.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    text_items = text_format.normalize_whitespace(event.text).split()
    if not text_items:
        output_text = "⛔️ Команда отписки чата на уведомления не распознана."
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
        )
        return

    # Если нет аргументов в команде
    if len(text_items) == 1:
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, text=DEL_NOTIFY_SUBSCRIBER_REFERENCE, parse_mode='HTML'
        )
        return

    # Если 1 аргумент в команде
    if len(text_items) == 2:
        if text_items[1] == '-list':
            send_notification_types(bot, event.from_chat)
            return

    # Если 2 аргумента в команде
    if len(text_items) == 3:
        if text_items[2] == '-desc':
            send_notification_description(bot, event.from_chat, text_items[1])
            return
        else:
            with db.get_db_session() as session:
                chat = db.crud.find_chat(session, text_items[1])
                notify_type = db.crud.find_notification_type(session, text_items[2])
                subscriber: Optional[db.NotificationSubscriber] = db.crud.find_one_record(
                    session, db.NotificationSubscriber,
                    {
                        db.NotificationSubscriber.chat_id: chat.id,
                        db.NotificationSubscriber.notification_type: notify_type.id
                    }
                ) if chat is not None and notify_type is not None else None

                is_correct = False
                if chat is None:
                    output_text = "⛔️ Чат с таким email не был найден в базе данных.\n"
                elif notify_type is None:
                    output_text = "⛔️ Такой тип уведомлений не был найден в базе данных.\n"
                elif not subscriber:
                    output_text = "✅ Чат не подписан на выбранный тип уведомлений.\n"
                else:
                    db.crud.delete_notifications_subscriber(session, subscriber)
                    output_text = (f"✅ Чат c email = '<i>{html.escape(chat.email)}</i>' "
                                   f"успешно отписан от уведомлений типа '<i>{html.escape(notify_type.type)}</i>'.\n")
                    is_correct = True
                    chat_email = chat.email
                    notify_type_type = notify_type.type

            # Направляем результат в текущий чат
            bot_extensions.send_text_or_raise(
                bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
            )

            if is_correct:
                # Сообщить администраторам об отписке чата от уведомлений
                admin_notify_text = (f"Чат с email = '{chat_email}' был отписан от уведомлений типа '{notify_type_type}' "
                                     f"(пользователем: {html.escape(event.from_chat)}).")
                notifications.send_notification_to_administrators(bot, admin_notify_text)

                # Сообщить в отписавшийся чат об отписке
                bot_extensions.send_text_or_raise(
                    bot, chat_email, f"📩 Система: Вы отписаны от уведомлений типа "
                                     f"'<i>{html.escape(notify_type_type)}</i>'",
                    parse_mode='HTML'
                )
            return

    # В остальных случаях выводим, что формат команды неверный
    send_invalid_command_format(bot, event.from_chat, Commands.DEL_NOTIFY_SUBSCRIBER.value, event.msgId)


@catch_and_log_exceptions
@administrator_access
def add_admin_command(bot: Bot, event: Event):
    """
    Обработать команду add_admin.
    Функция добавлять нового администратора в базу данных, если он ещё не администратор.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    text_items = text_format.normalize_whitespace(event.text).split()
    if not text_items:
        output_text = "⛔️ Команда добавления администратора не распознана."
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
        )
        return

    # Если нет аргументов в команде
    if len(text_items) == 1:
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, text=ADD_ADMIN_REFERENCE, parse_mode='HTML'
        )
        return

    # Если 1 аргумент в команде
    if len(text_items) == 2:
        with db.get_db_session() as session:
            chat = db.crud.find_chat(session, text_items[1])

            is_correct = False
            # Если чат не найден
            if chat is None:
                output_text = "⛔️ Чат с таким email не был найден в базе данных."
            # Если чат не пользователь
            elif chat.user is None:
                output_text = ("⛔️ Чат с таким email не принадлежит пользователю.\n\n"
                               f"❗️ Администратором можно сделать только чат типа '{html.escape(ChatType.PRIVATE.value)}'.")
            # Если пользователь уже админ
            elif chat.user.administrator is not None:
                output_text = f"✅ Чат c email = '{html.escape(text_items[1])}' уже является администратором."
            # Добавляем нового администратора
            else:
                admin = db.crud.create_administrator(session, chat.user, event.from_chat, date_and_time.get_current_date_moscow())
                output_text = f"✅ Чат c email = '{html.escape(text_items[1])}' успешно сделан администратором."
                is_correct = True
                chat_email = chat.email
                _, model_field, _ = db_records_format.find_config_model_format(db.get_tablename_by_model(db.Administrator))
                admin_text = (f"Добавлен новый администратор (пользователем: {html.escape(event.from_chat)}):\n"
                              f"{db_records_format.format_for_chat(admin, model_fields=model_field)}")

        bot_extensions.send_text_or_raise(
            bot, event.from_chat, output_text
        )

        if is_correct:
            # Сообщить администраторам о добавлении администратора
            notifications.send_notification_to_administrators(bot, admin_text)

            # Сообщить в чат нового администратора
            bot_extensions.send_text_or_raise(
                bot, chat_email, f"📩 Система: Вы стали администратором."
            )
        return

    # В остальных случаях выводим, что формат команды неверный
    send_invalid_command_format(bot, event.from_chat, Commands.ADD_ADMIN.value, event.msgId)


@catch_and_log_exceptions
@administrator_access
def del_admin_command(bot: Bot, event: Event):
    """
    Обработать команду del_admin.
    Функция отзывает доступ администратора у пользователя.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    text_items = text_format.normalize_whitespace(event.text).split()
    if not text_items:
        output_text = "⛔️ Команда удаления администратора не распознана."
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
        )
        return

    # Если нет аргументов в команде
    if len(text_items) == 1:
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, text=DEL_ADMIN_REFERENCE, parse_mode='HTML'
        )
        return

    # Если 1 аргумент в команде
    if len(text_items) == 2:
        with db.get_db_session() as session:
            chat = db.crud.find_chat(session, text_items[1])

            is_correct = False
            # Если чат не найден
            if chat is None:
                output_text = "⛔️ Чат с таким email не был найден в базе данных."
            # Если попытка удалить самого себя
            elif chat.email == event.from_chat:
                output_text = f"⛔️ Нельзя у самого себя отозвать доступ администратора."
            # Если чат не пользователь или не администратор
            elif chat.user is None or chat.user.administrator is None:
                output_text = "✅ Чат с таким email не является администратором."
            # Добавляем нового администратора
            else:
                admin = chat.user.administrator
                _, model_field, _ = db_records_format.find_config_model_format(db.get_tablename_by_model(db.Administrator))
                admin_text = (f"Отозван доступ администратора (пользователем: {html.escape(event.from_chat)}):\n"
                              f"{db_records_format.format_for_chat(admin, model_fields=model_field)}")
                chat_email = chat.email
                is_correct = db.crud.delete_administrator(session, admin)
                output_text = f"✅ У чата c email = '{html.escape(text_items[1])}' успешно отозван доступ администратора."

        bot_extensions.send_text_or_raise(
            bot, event.from_chat, output_text
        )

        if is_correct:
            # Сообщить администраторам о добавлении администратора
            notifications.send_notification_to_administrators(bot, admin_text)

            # Сообщить в чат нового администратора
            bot_extensions.send_text_or_raise(
                bot, chat_email, f"📩 Система: Вы больше не администратор."
            )
        return

    # В остальных случаях выводим, что формат команды неверный
    send_invalid_command_format(bot, event.from_chat, Commands.DEL_ADMIN.value, event.msgId)


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
        output_text = "⛔️ Команда удаления чата не распознана."
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
            chat = db.crud.find_chat(session, text_items[1])

            result = False
            if chat is not None:
                _, model_field, _ = db_records_format.find_config_model_format(db.get_tablename_by_model(db.Chat))
                admin_text = (f"Чат удалён (пользователем: {html.escape(event.from_chat)}):\n"
                              f"{db_records_format.format_for_chat(chat, model_fields=model_field)}")
                chat_email = chat.email
                result = db.crud.delete_chat(session, chat)

        if result:
            output_text = f"✅ Чат c email = '{html.escape(text_items[1])}' успешно удалён из базы данных."
        else:
            output_text = "⛔️ Чат с таким email не был найден в базе данных."

        bot_extensions.send_text_or_raise(
            bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
        )

        if result:
            # Сообщить администраторам
            notifications.send_notification_to_administrators(bot, admin_text)

            # Сообщить в чат изменённого объекта
            bot_extensions.send_text_or_raise(
                bot, chat_email, f"📩 Система: Вы больше не зарегистрированы в системе."
            )
        return

    # В остальных случаях выводим, что формат команды неверный
    send_invalid_command_format(bot, event.from_chat, Commands.DEL_CHAT.value, event.msgId)
