from typing import Optional
from bot.bot import Bot, Event
from bot.constant import ChatType
from app.utils import text_format
from app.core.bot_setup import Commands
from app import db

INFO_REQUEST_MESSAGE = ("❗️ Чтобы получить более подробную информацию о работе со мной и список доступных возможностей, "
                        f"отправьте мне команду <i>/{Commands.HELP.value}</i>.")


def start_command(bot: Bot, event: Event):
    """
    Обработка команды start.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    output_text = ("<b>Здравствуйте!\n"
                   "Моей основной задачей является сообщать о событиях компьютерных инцидентов, "
                   "произошедших в системе мониторинга.\n\n" +
                   INFO_REQUEST_MESSAGE)

    bot.send_text(event.from_chat, output_text, parse_mode='HTML')

    # Ищем чат в базе данных
    with db.get_db_session() as session:
        chat = db.crud.find_chat(session, event.from_chat)

    # Если чат не был найден
    if chat is None:
        send_not_found_chat(bot, event.from_chat, event.chat_type)


def help_command(bot: Bot, event: Event):
    """
    Обработка команды help.

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
    Обработка команды status.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    with db.get_db_session() as session:
        chat = db.crud.find_chat(session, event.from_chat)

    # Если приватный чат
    if event.chat_type == ChatType.PRIVATE.value:
        with db.get_db_session() as session:
            user = db.crud.find_user_by_chat(session, chat)
            # Если пользователь существует
            if user is not None:
                # Обновляем данные пользователя в базе данных до актуальных
                first_name: str = event.data['from']['firstName']
                last_name: Optional[str] = event.data['from']['lastName'] if event.data['from']['lastName'] else None
                db.crud.update_user(session, user, first_name, last_name)

        # Если пользователь не найден
        if user is None:
            send_not_found_chat(bot, event.from_chat, event.chat_type)
            return
        else:
            # Проверяем администратор ли пользователь и на какие уведомления подписан
            with db.get_db_session() as session:
                is_admin = db.crud.is_user_administrator(session, user)
                subscriber_notifications = db.crud.find_notifications_subscriber_by_chat(session, chat)

            output_text = "📍 <b>Статус пользователя</b>"

            output_text += f"\n\n🔹 email: <i>{chat.email}</i>"

            output_text += f"\n🔹 Имя: <i>{user.first_name}</i>"

            output_text += "\n🔹 Фамилия: " + (f"<i>{user.last_name}</i>" if user.last_name is not None else "")

            output_text += "\n🔹 Роль: " + ("<i>Администратор</i>" if is_admin else "<i>Пользователь</i>")

            output_text += "\n🔹 Подписки на уведомления: "

            # Если нет подписок:
            if not subscriber_notifications:
                output_text += "❌"
            else:
                # Список название подписок на уведомления
                types = [
                    db.crud.find_notification_type(session, item.notification_type).type
                    for item in subscriber_notifications
                ]

                output_text += "[" + ", ".join(types) + "]"

    else:
        with db.get_db_session() as session:
            group = db.crud.find_group_by_chat(session, chat)
            # Если группа существует
            if group is not None:
                # Обновляем данные группы в базе данных до актуальных
                title: str = event.data['chat']['title']
                db.crud.update_group(session, group, title)

        # Если группа не найден
        if group is None:
            send_not_found_chat(bot, event.from_chat, event.chat_type)
            return

        with db.get_db_session() as session:
            subscriber_notifications = db.crud.find_notifications_subscriber_by_chat(session, chat)

        output_text = "📍 <b>Статус группы</b>"

        output_text += f"\n\n🔹 Название: <i>{group.title}</i>"

        output_text += "\n🔹 Подписки на уведомления: "

        # Если нет подписок:
        if not subscriber_notifications:
            output_text += "❌"
        else:
            # Список название подписок на уведомления
            types = [
                db.crud.find_notification_type(session, item.notification_type).type
                for item in subscriber_notifications
            ]

            output_text += "[" + ", ".join(types) + "]"

    # Отправляем сообщение
    for message_text in text_format.split_text(output_text, 4096):
        bot.send_text(event.from_chat, message_text, parse_mode='HTML')


def unprocessed_command(bot: Bot, event: Event):
    """
    Обработка сообщений, которые не учитываются в боте.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    output_text = ("🍃 <i>Шелест листьев</i> 🍃\n\n"
                   "Я не знаю что с этим делать\n\n" +
                   INFO_REQUEST_MESSAGE)

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
                               "Чтобы начать работу, Вы должны быть зарегистрированы в моей системе.\n\n" +
                               INFO_REQUEST_MESSAGE)

    else:
        not_found_chat_text = ("⚠️ <b>Этого чата нет в моих списках зарегистрированных чатов</b>\n"
                               "Чтобы начать работу, чат должен быть добавлен в мои списки.\n\n" +
                               INFO_REQUEST_MESSAGE)

    bot.send_text(chat_id, not_found_chat_text, parse_mode='HTML')
