import json
from typing import List, Dict, Optional
import html
from bot.bot import Bot, Event
from app.utils import db_records_format
from app import db
from .helpers import (
    catch_and_log_exceptions, administrator_access, send_available_database_tables,
    make_callback_data, parse_callback_data
)
from .constants import (
    Commands, CallbackAction, GET_DATA_REFERENCE, DEL_CHAT_REFERENCE
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
            tables: List[str] = list(db.models.Base.metadata.tables.keys())
            if text_items[1] not in tables:
                not_found_text = "⛔️ <b>Таблицы с таким названием не существует.</b>"
                bot_extensions.send_text_or_raise(
                    bot, event.from_chat, not_found_text, reply_msg_id=event.msgId, parse_mode='HTML'
                )
            else:
                # Отправляем кнопку с предложением просмотра
                output_text = f"<b>Вы хотите получить записи таблицы '<i>{html.escape(text_items[1])}</i>'?</b>"
                markup = "{}".format(json.dumps([[
                    {
                        "text": "Открыть",
                        "callbackData": make_callback_data(CallbackAction.VIEW_DB, pg=0, tb=text_items[1]),
                        "style": "primary"
                    }
                ]]))
                bot_extensions.send_text_or_raise(
                    bot, event.from_chat, output_text, inline_keyboard_markup=markup, parse_mode='HTML'
                )
        return

    # В остальных случаях выводим, что формат команды неверный
    output_text = ("⛔️ <b>Некорректный формат команды.</b>\n"
                   f"Чтобы узнать какой формат необходим, отправьте мне <i>/{Commands.GET_DATA.value}</i>")
    bot_extensions.send_text_or_raise(
        bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
    )


@catch_and_log_exceptions
@administrator_access
def database_record_review(bot: Bot, event: Event):
    """
    Получить список записей заданной таблицы базы данных.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    query_id: str = event.data.get('queryId', None)
    callback: str = event.data.get('callbackData', None)

    if query_id is None or callback is None:
        raise ValueError("❌ queryId or callbackData missing.")

    bot.answer_callback_query(query_id=query_id, text="Request successful.", show_alert=False)

    # Убрать кнопку
    bot_extensions.edit_text_or_raise(
        bot, event.from_chat, event.msgId, "⏳ Ожидайте..."
    )

    cb = parse_callback_data(callback)
    page: int = cb['pg']
    table: str = cb['tb']

    config = next(
        (conf for conf in db_records_format.MODEL_FORMATS if conf[0].__tablename__ == table),
        None
    )
    if not config:
        text = f"⛔️ <b>Таблица '<i>{table}</i>' не поддерживается.</b>"
        bot_extensions.edit_text_or_raise(
            bot, event.from_chat, event.msgId, text, parse_mode='HTML'
        )
        return

    model, model_fields, page_size = config
    start = page * page_size + 1
    end = start + page_size - 1

    with db.get_db_session() as session:
        records = db.crud.get_records_range(session, model, start=start, end=end)
        total_records = db.crud.count_records(session, model)

    # Кнопки перехода
    button_back: Optional[Dict] = None
    button_next: Optional[Dict] = None

    if page > 0:
        button_back = {
            "text": "<< Назад",
            "callbackData": make_callback_data(CallbackAction.VIEW_DB, pg=page-1, tb=table),
            "style": "primary"
        }

    if end < total_records:
        button_next = {
            "text": "Дальше >>",
            "callbackData": make_callback_data(CallbackAction.VIEW_DB, pg=page+1, tb=table),
            "style": "primary"
        }

    # Собираем разметку
    markup: Optional[str] = None
    row: List[dict] = []
    if button_back:
        row.append(button_back)
    if button_next:
        row.append(button_next)
    if row:
        keyboard = [row]
        markup = json.dumps(keyboard)

    if not records:
        text = f"Список таблицы '{table}'\n\n📭 Записей нет."
        bot_extensions.edit_text_or_raise(
            bot, event.from_chat, event.msgId, text,  inline_keyboard_markup=markup
        )
        return

    format_records = db_records_format.format_for_chat(records, model_fields=model_fields)
    output_text = f"Список таблицы '{table}'\n\n{format_records}"
    bot_extensions.edit_text_or_raise(
        bot, event.from_chat, event.msgId, output_text, inline_keyboard_markup=markup
    )
    return


@catch_and_log_exceptions
@administrator_access
def del_chat_command(bot: Bot, event: Event):
    """
    Обработать команду del_chat.

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
    output_text = ("⛔️ <b>Некорректный формат команды.</b>\n"
                   f"Чтобы узнать какой формат необходим, отправьте мне <i>/{Commands.DEL_CHAT.value}</i>")
    bot_extensions.send_text_or_raise(
        bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
    )
