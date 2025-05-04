from enum import Enum
from bot.bot import Bot
from bot.handler import StartCommandHandler, HelpCommandHandler, CommandHandler, UnknownCommandHandler
from . import environment
from app import bot_handlers

# Объект бота
app = Bot(token=environment.BOT_TOKEN, name="monitor-flow-bot")


class Commands(Enum):
    START = "start"
    HELP = "help"
    STATUS = "status"
    MAN = "man"
    STOP = "stop"
    REGISTER = "register"
    NOTIFY_ON = "notify_on"
    NOTIFY_OFF = "notify_off"


def add_basic_commands_to_bot(bot: Bot):
    """
    Добавить базовые команды боту.
    :param bot: VKTeams bot.
    """
    bot.dispatcher.add_handler(
        StartCommandHandler(callback=bot_handlers.start_command)
    )

    bot.dispatcher.add_handler(
        HelpCommandHandler(callback=bot_handlers.help_command)
    )

    bot.dispatcher.add_handler(
        CommandHandler(command=Commands.STATUS, callback=bot_handlers.status_command)
    )

    # --- Unprocessed command ---
    bot.dispatcher.add_handler(
        UnknownCommandHandler(callback=bot_handlers.unprocessed_command)
    )
