from bot.bot import Bot
from bot.handler import StartCommandHandler, HelpCommandHandler, CommandHandler, UnknownCommandHandler
from . import environment
from app import bot_handlers

# Объект бота
app = Bot(token=environment.BOT_TOKEN, name="monitor-flow-bot")


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
        CommandHandler(command=bot_handlers.Commands.STATUS.value, callback=bot_handlers.status_command)
    )

    # --- Unprocessed command ---
    bot.dispatcher.add_handler(
        UnknownCommandHandler(callback=bot_handlers.unprocessed_command)
    )
