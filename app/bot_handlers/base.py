from typing import Dict, Any
import html
from bot.bot import Bot, Event
from bot.constant import ChatType
from app.utils import text_format
from app.core import bot_extensions
from app import db
from . import users, groups
from .helpers import (
    send_not_found_chat, send_notification_types, send_notification_types_access,
    send_notification_description, catch_and_log_exceptions, send_invalid_command_format
)
from .constants import (
    Commands, INFO_REQUEST_MESSAGE, NOTIFY_ON_REFERENCE, NOTIFY_OFF_REFERENCE,
    HELP_BASE_MESSAGE
)


@catch_and_log_exceptions
def start_command(bot: Bot, event: Event):
    """
    Обработать команду start.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    output_text = ("<b>Здравствуйте!</b>\n"
                   "Моей основной задачей является сообщать о событиях компьютерных инцидентов, "
                   "произошедших в системе мониторинга.\n\n"
                   f"{INFO_REQUEST_MESSAGE}")

    bot_extensions.send_text_or_raise(
        bot, event.from_chat, output_text, parse_mode='HTML'
    )

    # Ищем чат в базе данных
    with db.get_db_session() as session:
        chat = db.crud.find_chat(session, event.from_chat)

    # Если чат не был найден
    if chat is None:
        send_not_found_chat(bot, event.from_chat, event.chat_type)


def help_command(bot: Bot, event: Event):
    """
    Обработать команду help.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    # Начальный текст
    output_text = (f"{HELP_BASE_MESSAGE}\n\n"
                   "<b>--- Список команд:</b>\n\n")

    output_text += (
        f"🔹 <i>/{Commands.HELP.value}</i> - справка и список команд;\n"
        f"🔹 <i>/{Commands.REGISTER.value}</i> - регистрация в системе бота;\n"
        f"🔹 <i>/{Commands.SIGN_OUT.value}</i> - удаление текущей регистрации;\n"
        f"🔹 <i>/{Commands.STATUS.value}</i> - данные о регистрации, статусе и уведомлениях;\n"
        f"🔹 <i>/{Commands.START.value}</i> - возобновить отправку сообщений ботом и приветственное сообщение;\n"
        f"🔹 <i>/{Commands.NOTIFY_ON.value}</i> - подписка или просмотр данных уведомлений (отправляемых ботом);\n"
        f"🔹 <i>/{Commands.NOTIFY_OFF.value}</i> - отписка или просмотр данных уведомлений (отправляемых ботом)."
    )

    # Если приватный чат
    if event.chat_type == ChatType.PRIVATE.value:
        users.send_help_user(bot, event, output_text)
    else:
        groups.send_help_group(bot, event, output_text)


@catch_and_log_exceptions
def status_command(bot: Bot, event: Event):
    """
    Обработать команду status.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    # Собираем необходимые данные внутри одной сессии
    payload: Dict[str, Any] = {}
    with db.get_db_session() as session:
        chat = db.crud.find_chat(session, event.from_chat)
        if chat is None:
            send_not_found_chat(bot, event.from_chat, event.chat_type)
            return

        # Определяем, это пользователь или группа, и обновляем данные
        if chat.user is not None:
            # Обновляем поля пользователя
            first_name = event.data['from']['firstName']
            last_name = event.data['from'].get('lastName') or None
            db.crud.update_user(session, chat.user, first_name, last_name)

            payload.update({
                'title': 'Статус пользователя',
                'email': chat.email,
                'name_label': 'Имя',
                'name': chat.user.first_name,
                'surname_label': 'Фамилия',
                'surname': chat.user.last_name,
                'role': 'Администратор' if chat.user.administrator else None
            })
        elif chat.group is not None:
            # Обновляем название группы
            title = event.data['chat']['title']
            db.crud.update_group(session, chat.group, title)

            payload.update({
                'title': 'Статус группы',
                'name_label': 'Название',
                'name': chat.group.title,
                'role': None
            })
        else:
            send_not_found_chat(bot, event.from_chat, event.chat_type)
            return

        # Получаем подписки
        payload['subscriptions'] = [
            sub.notification_type_model.type
            for sub in chat.notification_subscribers
        ]

    # Формируем текст ответа
    lines = [f"📍 <b>{payload['title']}</b>\n"]

    if 'email' in payload:
        lines.append(f"\n🔹 email: <i>{html.escape(payload['email'])}</i>")

    lines.append(f"\n🔹 {payload['name_label']}: <i>{html.escape(payload['name'])}</i>")

    if payload.get('surname_label'):
        surname = payload.get('surname') or ''
        lines.append(f"\n🔹 {payload['surname_label']}: <i>{html.escape(surname)}</i>")

    if payload.get('role'):
        lines.append(f"\n🔹 Роль: <i>{html.escape(payload['role'])}</i>")

    lines.append("\n🔹 Подписки на уведомления: ")
    if not payload['subscriptions']:
        lines.append("❌")
    else:
        subs = ", ".join(payload['subscriptions'])
        lines.append(f"[{html.escape(subs)}]")

    output_text = ''.join(lines)

    bot_extensions.send_long_text(
        bot, event.from_chat, output_text, parse_mode='HTML'
    )


def register_command(bot: Bot, event: Event):
    """
    Обработать команду register.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    # Если приватный тип чата
    if event.chat_type == ChatType.PRIVATE.value:
        # Зарегистрировать нового пользователя
        users.register_user(bot, event)
    else:
        # Зарегистрировать новую группу
        groups.register_group(bot, event)


def sign_out_command(bot: Bot, event: Event):
    """
    Обработать команду sign_out.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    # Если приватный тип чата
    if event.chat_type == ChatType.PRIVATE.value:
        # Зарегистрировать нового пользователя
        users.delete_user_registration(bot, event)
    else:
        # Зарегистрировать новую группу
        groups.delete_group_registration(bot, event)


@catch_and_log_exceptions
def notify_on_command(bot: Bot, event: Event):
    """
    Обработать команду notify_on.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    text_items = text_format.normalize_whitespace(event.text).split()
    if not text_items:
        output_text = "⛔️ <b>Команда уведомлений не распознана.</b>"
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
        )
        return

    # Если нет аргументов в команде
    if len(text_items) == 1:
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, text=NOTIFY_ON_REFERENCE, parse_mode='HTML'
        )
        return

    # Если 1 аргумент в команде
    if len(text_items) == 2:
        if text_items[1] == '-list':
            send_notification_types(bot, event.from_chat)
            return
        elif text_items[1] == '-access':
            send_notification_types_access(bot, event.from_chat, True)
            return
        else:
            # Если приватный тип чата
            if event.chat_type == ChatType.PRIVATE.value:
                users.user_subscribe_notifications(bot, event, text_items[1])
            else:
                groups.group_subscribe_notifications(bot, event, text_items[1])
            return

    # Если 2 аргумента
    if len(text_items) == 3 and text_items[2] == '-desc':
        send_notification_description(bot, event.from_chat, text_items[1])
        return

    # В остальных случаях выводим, что формат команды неверный
    send_invalid_command_format(bot, event.from_chat, Commands.NOTIFY_ON.value, event.msgId)


@catch_and_log_exceptions
def notify_off_command(bot: Bot, event: Event):
    """
    Обработать команду notify_off.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    text_items = text_format.normalize_whitespace(event.text).split()
    if not text_items:
        output_text = "⛔️ <b>Команда уведомлений не распознана.</b>"
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
        )
        return

    # Если нет аргументов в команде
    if len(text_items) == 1:
        bot_extensions.send_text_or_raise(
            bot, event.from_chat, text=NOTIFY_OFF_REFERENCE, parse_mode='HTML'
        )
        return

    # Если 1 аргумент в команде
    if len(text_items) == 2:
        if text_items[1] == '-list':
            send_notification_types(bot, event.from_chat)
            return
        elif text_items[1] == '-access':
            send_notification_types_access(bot, event.from_chat, False)
            return
        else:
            # Если приватный тип чата
            if event.chat_type == ChatType.PRIVATE.value:
                users.user_unsubscribe_notifications(bot, event, text_items[1])
            else:
                groups.group_unsubscribe_notifications(bot, event, text_items[1])
            return

    # Если 2 аргумента
    if len(text_items) == 3 and text_items[2] == '-desc':
        send_notification_description(bot, event.from_chat, text_items[1])
        return

    # В остальных случаях выводим, что формат команды неверный
    send_invalid_command_format(bot, event.from_chat, Commands.NOTIFY_OFF.value, event.msgId)


@catch_and_log_exceptions
def unprocessed_command(bot: Bot, event: Event):
    """
    Обработать сообщения, которые не учитываются в боте.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    output_text = ("🍃 <i>Шелест листьев</i> 🍃\n\n"
                   "Я не знаю что с этим делать\n\n"
                   f"{INFO_REQUEST_MESSAGE}")

    bot_extensions.send_text_or_raise(
        bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
    )
