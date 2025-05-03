from bot.bot import Bot, Event
from bot.handler import MessageHandler
from app.core import bot_setup
from app.core import bot_extensions


def send_echo(bot: Bot, event: Event):
    """
    Отправить полученное сообщение в текущий чат.

    :param bot: VKTeams bot.
    :param event: Событие, полученное от сервера.
    """
    bot.send_text(event.from_chat, event.text)


if __name__ == "__main__":
    # --- Объект бота ---
    app = bot_setup.app

    app.dispatcher.add_handler(MessageHandler(callback=send_echo))

    app.start_polling()
    app.idle()
