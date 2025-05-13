from typing import Optional
import html
from bot.bot import Bot, Event
from bot.constant import ChatType
from app import db
from app.utils import date_and_time, text_format
from app.bot_handlers.helpers import (
    send_not_found_chat, catch_and_log_exceptions
)
from app.bot_handlers.constants import (
    Commands, INFO_REQUEST_MESSAGE, START_REQUEST_MESSAGE, HELP_BASE_MESSAGE
)


@catch_and_log_exceptions
def send_help_user(bot: Bot, event: Event, initial_text: str = ""):
    """
    Отправить пользователю информационное сообщение по работе с ботом.

    :param bot: VKTeams bot.
    :param event: Событие.
    :param initial_text: Начальный текст для отправки.
    """
    # Если нет начального текста добавляем стандартный
    if not initial_text:
        output_text = f"{HELP_BASE_MESSAGE}\n\n"
    else:
        output_text = f"{initial_text}\n\n"

    output_text += "<b>--- Список команд пользователя:</b>\n\n"

    output_text += (
        f"🔹 <i>/{Commands.STOP.value}</i> - запрет отправки сообщений ботом и удаление регистрации;\n"
        "(<b>Важно:</b> отправляя эту команду, бот больше не сможет вам ничего написать. "
        f"Для того, чтобы бот смог возобновить отправку сообщений, необходимо отправить <i>/{Commands.START.value}</i>)."
    )

    # Отправляем текст по частям (не превышая лимит)
    for part in text_format.split_text(output_text, 4096):
        bot.send_text(event.from_chat, part, parse_mode='HTML')


@catch_and_log_exceptions
def register_user(bot: Bot, event: Event):
    """
    Зарегистрировать нового пользователя, если не зарегистрирован.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    # Если не приватный тип чата
    if event.chat_type != ChatType.PRIVATE.value:
        raise TypeError("❌ Attempting to create a user whose chat type is not private.\n\n"
                        f"- from_chat: {str(event.from_chat)}")

    with db.get_db_session() as session:
        chat = db.crud.find_chat(session, event.from_chat)

        # Если чат не существует, регистрируем новый чат
        if chat is None:
            chat = db.crud.create_chat(session, event.from_chat, event.chat_type)

        # Если пользователь существует
        if chat.user is not None:
            output_text = "⚠️ <b>Вы уже зарегистрированы в системе бота, повторная регистрация не требуется.</b>"
        else:
            first_name: str = event.data['from']['firstName']
            last_name: Optional[str] = event.data['from']['lastName'] if event.data['from']['lastName'] else None

            user = db.crud.create_user(session, chat, first_name, last_name)

            # Если нет ни одного администратора, делаем созданного пользователя администратором
            if db.crud.count_records(session, db.Administrator) == 0:
                db.crud.create_administrator(
                    session, user, event.message_author['userId'], date_and_time.get_current_date_moscow()
                )

            output_text = ("✅ <b>Вы успешно зарегистрированы в системе бота.</b>\n\n"
                           f"{INFO_REQUEST_MESSAGE}")

    # Отправляем сообщение в текущий чат
    bot.send_text(event.from_chat, output_text, parse_mode='HTML')


@catch_and_log_exceptions
def delete_user_registration(bot: Bot, event: Event):
    """
    Удалить регистрацию пользователя, если зарегистрирован.

    :param bot: VKTeams bot.
    :param event: Событие.
    """
    with db.get_db_session() as session:
        chat = db.crud.find_chat(session, event.from_chat)

        # Если не приватный тип чата
        if chat is not None and chat.chat_type_model.type != ChatType.PRIVATE.value:
            raise TypeError("❌ Attempting to remove a user whose chat type is not private.\n\n"
                            f"- from_chat: {str(event.from_chat)}")

        # Если пользователь существует, то удаляем
        user = db.crud.find_user_by_chat(session, chat)
        if user is not None:
            db.crud.delete_user(session, user, True)

        # Если чат существует, удаляем
        if db.crud.find_chat(session, event.from_chat) is not None:
            db.crud.delete_chat(session, chat)

    # Отправляем сообщение в текущий чат
    output_text = ("✅ <b>Вы не зарегистрированы в системе бота.</b>\n\n"
                   f"{START_REQUEST_MESSAGE}\n\n"
                   f"{INFO_REQUEST_MESSAGE}")
    bot.send_text(event.from_chat, output_text, parse_mode='HTML')


@catch_and_log_exceptions
def user_subscribe_notifications(bot: Bot, event: Event, notification_type_name: str):
    """
    Подписаться пользователю на уведомления заданного типа.

    :param bot: VKTeams bot.
    :param event: Событие.
    :param notification_type_name: Название типа уведомления, на который оформляется подписка.
    """
    with db.get_db_session() as session:
        chat = db.crud.find_chat(session, event.from_chat)

        if chat is None or chat.user is None:
            register_user(bot, event)
            chat = db.crud.find_chat(session, event.from_chat)

        is_admin = db.crud.is_user_administrator(session, chat.user)
        notification_type = db.crud.find_notification_type(session, notification_type_name)

        if notification_type is None:
            output_text = f"⚠️ <b>Типа уведомления '<i>{html.escape(notification_type_name)}</i>' не существует.</b>"
        elif any(item.notification_type == notification_type.id for item in chat.notification_subscribers):
            output_text = f"✅ <b>Вы уже подписаны на тип уведомления '<i>{html.escape(notification_type_name)}</i>'.</b>"
        elif is_admin:
            db.crud.add_notification_subscriber(
                session, chat, notification_type, chat.email, date_and_time.get_current_date_moscow()
            )
            output_text = f"✅ <b>Вы успешно подписались на уведомления типа '<i>{html.escape(notification_type.type)}</i>'</b>"
        else:
            raise ValueError("⛔ Unprocessed case")

    bot.send_text(event.from_chat, text=output_text, parse_mode='HTML')


@catch_and_log_exceptions
def user_unsubscribe_notifications(bot: Bot, event: Event, notification_type_name: str):
    """
    Отписаться пользователю от уведомлений заданного типа.

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
            output_text = f"⚠️ <b>Типа уведомления '<i>{html.escape(notification_type_name)}</i>' не существует.</b>"
        elif all(item.notification_type != notification_type.id for item in chat.notification_subscribers):
            output_text = f"✅ <b>Вы не подписаны на тип уведомления '<i>{html.escape(notification_type_name)}</i>'.</b>"
        else:
            db.crud.delete_notification_subscriber_by_data(session, chat, notification_type)
            output_text = f"✅ <b>Вы отписались от уведомлений типа '<i>{html.escape(notification_type_name)}</i>'.</b>"

    bot.send_text(event.from_chat, text=output_text, parse_mode='HTML')
