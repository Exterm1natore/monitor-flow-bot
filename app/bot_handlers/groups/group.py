import html
from bot.bot import Bot, Event
from bot.constant import ChatType
from app import db
from app.utils import date_and_time
from app.core import bot_extensions
from app.bot_handlers.helpers import (
    send_not_found_chat, catch_and_log_exceptions, administrator_access
)
from app.bot_handlers.constants import (
    Commands, INFO_REQUEST_MESSAGE, START_REQUEST_MESSAGE, HELP_BASE_MESSAGE
)


@catch_and_log_exceptions
def send_help_group(bot: Bot, event: Event, initial_text: str = ""):
    """
    Отправить в группу информационное сообщение по работе с ботом.

    :param bot: VKTeams bot.
    :param event: Событие.
    :param initial_text: Начальный текст для отправки.
    """
    # Если нет начального текста добавляем стандартный
    if not initial_text:
        output_text = f"{HELP_BASE_MESSAGE}\n\n"
    else:
        output_text = f"{initial_text}\n\n"

    output_text += "<b>--- Список команд группы:</b>\n\n"

    output_text += (
        f"🔹 /{Commands.START.value} - приветственное сообщение.\n"
    )

    bot_extensions.send_long_text(
        bot, event.from_chat, output_text, parse_mode='HTML'
    )


@catch_and_log_exceptions
@administrator_access
def register_group(bot: Bot, event: Event):
    """
    Зарегистрировать новую группу, если не зарегистрирована.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    # Если приватный тип чата
    if event.chat_type == ChatType.PRIVATE.value:
        raise TypeError("❌ Attempting to create a group that has a chat type of private.\n\n"
                        f"- from_chat: {str(event.from_chat)}")

    with db.get_db_session() as session:
        chat = db.crud.find_chat(session, event.from_chat)

        # Если чат не существует, регистрируем новый чат
        if chat is None:
            chat = db.crud.create_chat(session, event.from_chat, event.chat_type)

        # Если группа существует
        if chat.group is not None:
            output_text = "⚠️ Эта группа уже зарегистрирована в системе бота, повторная регистрация не требуется."
        else:
            title: str = event.data['chat']['title']

            db.crud.create_group(session, chat, title)

            output_text = ("✅ Группа успешно зарегистрированы в системе бота.\n\n"
                           f"{INFO_REQUEST_MESSAGE}")

    # Отправляем сообщение в текущий чат
    bot_extensions.send_text_or_raise(
        bot, event.from_chat, output_text, parse_mode='HTML'
    )


@catch_and_log_exceptions
@administrator_access
def delete_group_registration(bot: Bot, event: Event):
    """
    Удалить регистрацию группы, если зарегистрирована.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    with db.get_db_session() as session:
        chat = db.crud.find_chat(session, event.from_chat)

        # Если приватный тип чата
        if chat is not None and chat.chat_type_model.type == ChatType.PRIVATE.value:
            raise TypeError("❌ Attempting to remove a group whose chat type is private.\n\n"
                            f"- from_chat: {str(event.from_chat)}")

        # Если группа существует, то удаляем
        group = db.crud.find_group_by_chat(session, chat)
        if group is not None:
            db.crud.delete_group(session, group, True)

        # Если чат существует, удаляем
        if db.crud.find_chat(session, event.from_chat) is not None:
            db.crud.delete_chat(session, chat)

    # Отправляем сообщение в текущий чат
    output_text = ("✅ Группа не зарегистрированы в системе бота.\n\n"
                   f"{START_REQUEST_MESSAGE}\n\n"
                   f"{INFO_REQUEST_MESSAGE}")
    bot_extensions.send_text_or_raise(
        bot, event.from_chat, output_text, parse_mode='HTML'
    )


@catch_and_log_exceptions
@administrator_access
def group_subscribe_notifications(bot: Bot, event: Event, notification_type_name: str):
    """
    Подписаться группе на уведомления заданного типа.

    :param bot: VKTeams bot.
    :param event: Событие.
    :param notification_type_name: Название типа уведомления, на который оформляется подписка.
    """
    with db.get_db_session() as session:
        chat = db.crud.find_chat(session, event.from_chat)

        if chat is None or chat.group is None:
            register_group(bot, event)
            chat = db.crud.find_chat(session, event.from_chat)

        notification_type = db.crud.find_notification_type(session, notification_type_name)

        if notification_type is None:
            output_text = f"⚠️ Такого типа уведомления не существует."
        elif any(item.notification_type == notification_type.id for item in chat.notification_subscribers):
            output_text = f"✅ Группа уже подписана на тип уведомления '{html.escape(notification_type_name)}'."
        else:
            db.crud.add_notification_subscriber(
                session, chat, notification_type, event.message_author['userId'], date_and_time.get_current_date_moscow()
            )
            output_text = f"✅ Группа успешно подписана на уведомления типа '{html.escape(notification_type.type)}'."

    bot_extensions.send_text_or_raise(
        bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
    )


@catch_and_log_exceptions
@administrator_access
def group_unsubscribe_notifications(bot: Bot, event: Event, notification_type_name: str):
    """
    Отписаться группе от уведомлений заданного типа.

    :param bot: VKTeams bot.
    :param event: Событие.
    :param notification_type_name: Название типа уведомления, на которую отменяется подписка.
    """
    with db.get_db_session() as session:
        chat = db.crud.find_chat(session, event.from_chat)

        if chat is None:
            send_not_found_chat(bot, event.from_chat, event.chat_type)
            return

        notification_type = db.crud.find_notification_type(session, notification_type_name)

        if notification_type is None:
            output_text = f"⚠️ Такого типа уведомления не существует."
        elif all(item.notification_type != notification_type.id for item in chat.notification_subscribers):
            output_text = f"✅ Группа не подписана на тип уведомления '{html.escape(notification_type_name)}'."
        else:
            db.crud.delete_notification_subscriber_by_data(session, chat, notification_type)
            output_text = f"✅ Группа отписана от уведомлений типа '{html.escape(notification_type_name)}'."

    bot_extensions.send_text_or_raise(
        bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
    )
