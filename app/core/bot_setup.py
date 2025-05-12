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
        CommandHandler(command=bot_handlers.Commands.REGISTER.value, callback=bot_handlers.register_command)
    )

    bot.dispatcher.add_handler(
        CommandHandler(command=[bot_handlers.Commands.STOP.value, bot_handlers.Commands.SIGN_OUT.value],
                       callback=bot_handlers.sign_out_command)
    )

    bot.dispatcher.add_handler(
        CommandHandler(command=bot_handlers.Commands.STATUS.value, callback=bot_handlers.status_command)
    )

    bot.dispatcher.add_handler(
        CommandHandler(command=bot_handlers.Commands.NOTIFY_ON.value, callback=bot_handlers.notify_on_command)
    )

    bot.dispatcher.add_handler(
        CommandHandler(command=bot_handlers.Commands.NOTIFY_OFF.value, callback=bot_handlers.notify_off_command)
    )

    # --- Unprocessed command ---
    bot.dispatcher.add_handler(
        UnknownCommandHandler(callback=bot_handlers.unprocessed_command)
    )
