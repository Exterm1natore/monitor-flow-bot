from bot.bot import Bot
from . import environment

# Объект бота
app = Bot(token=environment.BOT_TOKEN, name="monitor-flow-bot")
