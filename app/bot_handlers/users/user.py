from typing import Optional
import logging
import html
from bot.bot import Bot, Event
from bot.constant import ChatType
from app import db
from app.utils import date_and_time, db_records_format
from app.core import bot_extensions
from app.bot_handlers.helpers import (
    send_not_found_chat, catch_and_log_exceptions
)
from app.bot_handlers.constants import (
    Commands, INFO_REQUEST_MESSAGE, START_REQUEST_MESSAGE, HELP_BASE_MESSAGE
)
from app.bot_handlers import notifications


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
        f"🔹 /{Commands.START.value} - возобновить отправку сообщений ботом и приветственное сообщение;\n"
        f"🔹 /{Commands.STOP.value} - запрет отправки сообщений ботом и удаление регистрации;\n"
        "(<b>Важно:</b> отправляя эту команду, бот больше не сможет вам ничего написать."
        f"Для того, чтобы бот смог возобновить отправку сообщений, необходимо отправить <i>/{Commands.START.value}</i>)."
    )

    with db.get_db_session() as session:
        chat = db.crud.find_chat(session, event.from_chat)
        is_admin: bool = chat.user.administrator is not None if chat is not None else False

    if is_admin:
        output_text += "\n\n<b>--- Список команд администратора:</b>\n\n"

        output_text += (f"🔹 /{Commands.GET_DATA.value} - просмотр записей базы данных приложения;\n"
                        f"🔹 /{Commands.FIND_DATA.value} - поиск записей базы данных приложения по заданному условию;\n"
                        f"🔹 /{Commands.ADD_NOTIFY_SUBSCRIBER.value} - оформление подписки на уведомления (отправляемых ботом) "
                        f"для заданного чата;\n"
                        f"🔹 /{Commands.DEL_NOTIFY_SUBSCRIBER.value} - отписка от уведомлений (отправляемых ботом) "
                        f"для заданного чата;\n"
                        f"🔹 /{Commands.ADD_ADMIN.value} - добавление нового администратора;\n"
                        f"🔹 /{Commands.DEL_ADMIN.value} - отзыв доступа администратора;\n"
                        f"🔹 /{Commands.DEL_CHAT.value} - удаление чата из базы данных приложения.\n")

    bot_extensions.send_long_text(
        bot, event.from_chat, output_text, parse_mode='HTML'
    )


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
        is_register = False
        if chat.user is not None:
            output_text = "⚠️ Вы уже зарегистрированы в системе бота, повторная регистрация не требуется."
        else:
            first_name: str = event.data['from']['firstName']
            last_name: Optional[str] = event.data['from']['lastName'] if event.data['from']['lastName'] else None

            user = db.crud.create_user(session, chat, first_name, last_name)

            # Если нет ни одного администратора, делаем созданного пользователя администратором
            if db.crud.count_records(session, db.Administrator) == 0:
                db.crud.create_administrator(
                    session, user, event.message_author['userId'], date_and_time.get_current_date_moscow()
                )
            output_text = ("✅ Вы успешно зарегистрированы в системе бота.\n\n"
                           f"{INFO_REQUEST_MESSAGE}")

            is_register = True
            _, model_fields, _ = db_records_format.find_config_model_format(db.get_tablename_by_model(db.User))
            record_format = db_records_format.format_for_chat(user, model_fields=model_fields)
            admin_request_text = f"🆕 Новый пользователь зарегистрирован.\n\nДанные:\n{record_format}"

    # Отправляем сообщение в текущий чат
    bot_extensions.send_text_or_raise(
        bot, event.from_chat, output_text, parse_mode='HTML'
    )

    # Оповещение для администраторов
    if is_register:
        try:
            notifications.send_notification_to_administrators(bot, admin_request_text)
        except Exception as e:
            logging.getLogger(__name__).exception(e)


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
        if chat and chat.chat_type_model.type != ChatType.PRIVATE.value:
            raise TypeError("❌ Attempting to remove a user whose chat type is not private.\n\n"
                            f"- from_chat: {str(event.from_chat)}")

        # Если пользователь существует, то удаляем
        user = chat.user if chat else None
        if user is not None:
            db.crud.delete_user(session, user, True)

        # Если чат существует, удаляем
        if db.crud.find_chat(session, event.from_chat) is not None:
            db.crud.delete_chat(session, chat)

    # Отправляем сообщение в текущий чат
    output_text = ("✅ Вы не зарегистрированы в системе бота.\n\n"
                   f"{START_REQUEST_MESSAGE}\n\n"
                   f"{INFO_REQUEST_MESSAGE}")

    bot_extensions.send_text_or_raise(
        bot, event.from_chat, output_text, parse_mode='HTML'
    )


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

        is_admin = chat.user.administrator is not None
        notification_type = db.crud.find_notification_type(session, notification_type_name)

        is_subscribe = False
        if notification_type is None:
            output_text = f"⚠️ Такого типа уведомления не существует."
        elif any(item.notification_type == notification_type.id for item in chat.notification_subscribers):
            output_text = f"✅ Вы уже подписаны на тип уведомления '{html.escape(notification_type_name)}'."
        elif is_admin:
            db.crud.add_notification_subscriber(
                session, chat, notification_type, chat.email, date_and_time.get_current_date_moscow()
            )
            output_text = f"✅ Вы успешно подписались на уведомления типа '{html.escape(notification_type.type)}'."

            is_subscribe = True
            admin_request_text = (f"Пользователь с email = '{event.from_chat}' подписался на "
                                  f"уведомления типа '{notification_type.type}'.")
        else:
            is_subscribe = True
            _, model_fields, _ = db_records_format.find_config_model_format(db.get_tablename_by_model(db.User))
            record_format = db_records_format.format_for_chat(chat.user, model_fields=model_fields)
            admin_request_text = (f"❗️ Пользователь отправил запрос подписки на уведомления типа '{notification_type.type}'.\n\n"
                                  f"Данные пользователя:\n"
                                  f"{record_format}\n\n"
                                  f"Необходимо вручную подписать пользователя не администратора на заданный тип уведомлений.\n"
                                  f"Чтобы подписать пользователя воспользуйтесь командой /{Commands.ADD_NOTIFY_SUBSCRIBER.value} ")

            output_text = (f"❇️ Запрос подписки на уведомления типа '{html.escape(notification_type.type)}' отправлен.\n"
                           f"Ожидайте, когда его одобрят. После одобрения вам придёт сообщение об успешной подписке.")

    bot_extensions.send_text_or_raise(
        bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
    )

    # Оповещение для администраторов
    if is_subscribe:
        try:
            notifications.send_notification_to_administrators(bot, admin_request_text)
        except Exception as e:
            logging.getLogger(__name__).exception(e)


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

        is_unsubscribe = False
        if notification_type is None:
            output_text = f"⚠️ Такого типа уведомления не существует."
        elif all(item.notification_type != notification_type.id for item in chat.notification_subscribers):
            output_text = f"✅ Вы не подписаны на тип уведомления '{html.escape(notification_type_name)}'."
        else:
            admin_request_text = (f"Пользователь с email = '{event.from_chat}' отписался от "
                                  f"уведомлений типа '{notification_type.type}'.")
            is_unsubscribe = db.crud.delete_notification_subscriber_by_data(session, chat, notification_type)
            output_text = f"✅ Вы отписались от уведомлений типа '{html.escape(notification_type_name)}'."

    bot_extensions.send_text_or_raise(
        bot, event.from_chat, output_text, reply_msg_id=event.msgId, parse_mode='HTML'
    )

    # Оповещение для администраторов
    if is_unsubscribe:
        try:
            notifications.send_notification_to_administrators(bot, admin_request_text)
        except Exception as e:
            logging.getLogger(__name__).exception(e)
