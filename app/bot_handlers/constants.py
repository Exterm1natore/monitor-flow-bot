from enum import Enum, unique


@unique
class Commands(Enum):
    HELP = "help"
    REGISTER = "register"
    SIGN_OUT = "sign_out"
    STATUS = "status"
    STOP = "stop"
    START = "start"
    NOTIFY_ON = "notify_on"
    NOTIFY_OFF = "notify_off"


@unique
class NotificationTypes(Enum):
    SYSTEM = 'system'
    ZABBIX = 'zabbix'


INFO_REQUEST_MESSAGE = ("❗️ Чтобы получить более подробную информацию о работе со мной и список доступных возможностей, "
                        f"отправьте мне команду <i>/{Commands.HELP.value}</i>.")
START_REQUEST_MESSAGE = ("❗️ Чтобы снова зарегистрироваться в системе, "
                         f"отправьте мне команду <i>/{Commands.REGISTER.value}</i>")

NOTIFY_ON_REFERENCE = (f"<b>Формат: /{Commands.NOTIFY_ON.value} [option] ...</b>\n\n"
                       "- Команда предназначена для подписки на определённый тип уведомления.\n\n"
                       "<b>Список опций:</b>\n"
                       "🔹 '<i>-list</i>' - получить список всех типов уведомлений для подписки;\n"
                       "🔹 &lt;<i>название типа уведомления</i>&gt; '<i>-desc</i>' - получить описание типа уведомления;\n"
                       "🔹 '<i>-access</i>' - посмотреть доступные для подписки типы уведомлений;\n"
                       "🔹 &lt;<i>название типа уведомления</i>&gt; - оформить подписку на заданный тип уведомления.")

NOTIFY_OFF_REFERENCE = (f"<b>Формат: /{Commands.NOTIFY_OFF.value} [option] ...</b>\n\n"
                        "- Команда предназначена для отписки от определённого типа уведомления.\n\n"
                        "<b>Список опций:</b>\n"
                        "🔹 '<i>-list</i>' - получить список всех типов уведомлений для подписки;\n"
                        "🔹 &lt;<i>название типа уведомления</i>&gt; '<i>-desc</i>' - получить описание типа уведомления;\n"
                        "🔹 '<i>-access</i>' - посмотреть доступные для отписки типы уведомлений;\n"
                        "🔹 &lt;<i>название типа уведомления</i>&gt; - отменить подписку на заданный тип уведомления.")

HELP_BASE_MESSAGE = "<b>Этот бот предназначен для отправки событий, произошедших в отслеживаемых системах.</b>"
