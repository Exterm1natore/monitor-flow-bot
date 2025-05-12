from typing import Dict, Any
import html
from bot.bot import Bot, Event
from bot.constant import ChatType
from app.utils import text_format
from app import db
from .constants import (
    Commands, INFO_REQUEST_MESSAGE, NOTIFY_ON_REFERENCE, NOTIFY_OFF_REFERENCE
)


def start_command(bot: Bot, event: Event):
    """
    Обработать команду start.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    output_text = ("<b>Здравствуйте!\n"
                   "Моей основной задачей является сообщать о событиях компьютерных инцидентов, "
                   "произошедших в системе мониторинга.\n\n"
                   f"{INFO_REQUEST_MESSAGE}")

    bot.send_text(event.from_chat, output_text, parse_mode='HTML')

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
    output_text = "Этот бот информирует о событиях компьютерных инцидентов, произошедших в системе мониторинга.\n\n"

    # Если приватный чат
    if event.chat_type == ChatType.PRIVATE.value:
        output_text += "<b>--- Список доступных команд:</b>\n\n"

        output_text += (f"🔹 <i>/{Commands.HELP.value}</i> - получить справку по работе с ботом и список доступных команд;\n"
                        f"🔹 <i>/{Commands.MAN.value}</i> - получить мануал по работе с ботом, с описанием его действий;\n"
                        f"🔹 <i>/{Commands.STATUS.value}</i> - получить данные о регистрации и статусе с системе бота;\n"
                        f"🔹 <i>/{Commands.STOP.value}</i> - удалить себя из системы бота и запретить боту отправлять сообщения;\n"
                        f"🔹 <i>/{Commands.START.value}</i> - разрешить боту отправлять сообщения (если было запрещено).")

        with db.get_db_session() as session:
            user = db.crud.find_user_by_chat(session, db.crud.find_chat(session, event.from_chat))
            is_admin = db.crud.is_user_administrator(session, user) if user is not None else False

        # Если пользователь является администратором
        if is_admin:
            output_text += "\n\n<b>--- Список команд администратора:</b>\n\n"

            output_text += "🔹 <i>/</i>"
    else:
        output_text += "<b>--- Список доступных команд:</b>\n\n"

    bot.send_text(event.from_chat, output_text, parse_mode='HTML')


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

    # Отправляем текст по частям (не превышая лимит)
    for part in text_format.split_text(output_text, 4096):
        bot.send_text(event.from_chat, part, parse_mode='HTML')


def register_command(bot: Bot, event: Event):
    """
    Обработать команду register.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    # Если приватный тип чата
    if event.chat_type == ChatType.PRIVATE.value:
        # Зарегистрировать нового пользователя
        from .users import register_user
        register_user(bot, event)
    else:
        # Зарегистрировать новую группу
        from .groups import register_group
        register_group(bot, event)


def sign_out_command(bot: Bot, event: Event):
    """
    Обработать команду sign_out.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    # Если приватный тип чата
    if event.chat_type == ChatType.PRIVATE.value:
        # Зарегистрировать нового пользователя
        from .users import delete_user_registration
        delete_user_registration(bot, event)
    else:
        # Зарегистрировать новую группу
        from .groups import delete_group_registration
        delete_group_registration(bot, event)


def notify_on_command(bot: Bot, event: Event):
    """
    Обработать команду notify_on.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    text_items = text_format.normalize_whitespace(event.text).split()
    if not text_items:
        output_text = "⛔️ <b>Команда уведомлений не распознана.</b>"
        bot.send_text(event.from_chat, text=output_text, reply_msg_id=event.msgId, parse_mode='HTML')
        return

    # Если нет аргументов в команде
    if len(text_items) == 1:
        bot.send_text(event.from_chat, text=NOTIFY_ON_REFERENCE, parse_mode='HTML')
        return

    # Если 1 аргумент в команде
    if len(text_items) == 2:
        if text_items[1] == '-list':
            send_notification_types(bot, event.from_chat)
        elif text_items[1] == '-access':
            send_notification_types_access(bot, event.from_chat, True)
        else:
            # Если приватный тип чата
            if event.chat_type == ChatType.PRIVATE.value:
                from .users import user_subscribe_notifications
                user_subscribe_notifications(bot, event, text_items[1])
            else:
                from .groups import group_subscribe_notifications
                group_subscribe_notifications(bot, event, text_items[1])
        return

    # Если 2 аргумента
    if len(text_items) == 3 and text_items[2] == '-desc':
        send_notification_description(bot, event.from_chat, text_items[1])
        return

    # В остальных случаях выводим, что формат команды неверный
    output_text = ("⛔️ <b>Некорректный формат команды.</b>\n"
                   f"Чтобы узнать какой формат необходим, отправьте мне <i>/{Commands.NOTIFY_ON.value}</i>")
    bot.send_text(event.from_chat, text=output_text, reply_msg_id=event.msgId, parse_mode='HTML')


def notify_off_command(bot: Bot, event: Event):
    """
    Обработать команду notify_off.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    text_items = text_format.normalize_whitespace(event.text).split()
    if not text_items:
        output_text = "⛔️ <b>Команда уведомлений не распознана.</b>"
        bot.send_text(event.from_chat, text=output_text, reply_msg_id=event.msgId, parse_mode='HTML')
        return

    # Если нет аргументов в команде
    if len(text_items) == 1:
        bot.send_text(event.from_chat, text=NOTIFY_OFF_REFERENCE, parse_mode='HTML')
        return

    # Если 1 аргумент в команде
    if len(text_items) == 2:
        if text_items[1] == '-list':
            send_notification_types(bot, event.from_chat)
        elif text_items[1] == '-access':
            send_notification_types_access(bot, event.from_chat, False)
        else:
            # Если приватный тип чата
            if event.chat_type == ChatType.PRIVATE.value:
                from .users import user_unsubscribe_notifications
                user_unsubscribe_notifications(bot, event, text_items[1])
            else:
                from .groups import group_unsubscribe_notifications
                group_unsubscribe_notifications(bot, event, text_items[1])
        return

    # Если 2 аргумента
    if len(text_items) == 3 and text_items[2] == '-desc':
        send_notification_description(bot, event.from_chat, text_items[1])
        return

    # В остальных случаях выводим, что формат команды неверный
    output_text = ("⛔️ <b>Некорректный формат команды.</b>\n"
                   f"Чтобы узнать какой формат необходим, отправьте мне <i>/{Commands.NOTIFY_OFF.value}</i>")
    bot.send_text(event.from_chat, text=output_text, reply_msg_id=event.msgId, parse_mode='HTML')


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

    for part in text_format.split_text(output_text, 4096):
        bot.send_text(chat_id, text=part, parse_mode='HTML')


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

    for part in text_format.split_text(output_text, 4096):
        bot.send_text(chat_id, text=part, parse_mode='HTML')


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

    for part in text_format.split_text(output_text, 4096):
        bot.send_text(chat_id, text=part, parse_mode='HTML')


def unprocessed_command(bot: Bot, event: Event):
    """
    Обработать сообщения, которые не учитываются в боте.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    output_text = ("🍃 <i>Шелест листьев</i> 🍃\n\n"
                   "Я не знаю что с этим делать\n\n"
                   f"{INFO_REQUEST_MESSAGE}")

    bot.send_text(event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode="HTML")


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

    bot.send_text(chat_id, not_found_chat_text, parse_mode='HTML')
