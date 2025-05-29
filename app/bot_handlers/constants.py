from enum import Enum, unique


@unique
class Commands(Enum):
    # --- base commands
    HELP = "help"
    REGISTER = "register"
    SIGN_OUT = "sign_out"
    STATUS = "status"
    STOP = "stop"
    START = "start"
    NOTIFY_ON = "notify_on"
    NOTIFY_OFF = "notify_off"

    # --- admin commands
    GET_DATA = "get_data"
    FIND_DATA = "find_data"
    ADD_NOTIFY_SUBSCRIBER = "add_notify_subscriber"
    DEL_NOTIFY_SUBSCRIBER = "del_notify_subscriber"
    DEL_CHAT = "del_chat"


@unique
class CallbackAction(Enum):
    VIEW_DB = "view_db"
    FIND_DB = "find_db"

    @staticmethod
    def is_valid(value: str) -> bool:
        """Проверяет, является ли значение допустимым действием CallbackAction."""
        return any(value == action.value for action in CallbackAction)


@unique
class NotificationTypes(Enum):
    SYSTEM = 'system'
    ZABBIX = 'zabbix'


INFO_REQUEST_MESSAGE = ("❗️ Чтобы получить более подробную информацию о работе со мной и список доступных возможностей, "
                        f"отправьте мне команду /{Commands.HELP.value} ")
START_REQUEST_MESSAGE = ("❗️ Чтобы снова зарегистрироваться в системе, "
                         f"отправьте мне команду /{Commands.REGISTER.value} ")

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

GET_DATA_REFERENCE = (f"<b>Формат: /{Commands.GET_DATA.value} [option] ...</b>\n\n"
                      f"- Команда предназначена для просмотра записей базы данных.\n\n"
                      f"<b>Список опций:</b>\n"
                      f"🔹 '<i>-list</i>' - получить список всех доступных таблиц базы данных;\n"
                      f"🔹 &lt;<i>название таблицы</i>&gt; - получить список записей заданной таблицы.")

FIND_DATA_REFERENCE = (f"<b>Формат: /{Commands.FIND_DATA.value} [option] ...</b>\n\n"
                       f"- Команда предназначена для просмотра записей базы данных, удовлетворяющих условию поиска.\n"
                       f"  Для строковых данных производится частичный поиск.\n"
                       f"  Для данных с типом DATETIME производится поиск только по дате (разделители '-' или '.').\n\n"
                       f"<b>Список опций:</b>\n"
                       f"🔹 '<i>-list</i>' - получить список всех доступных таблиц базы данных;\n"
                       f"🔹 &lt;<i>название таблицы</i>&gt; '<i>-list</i>' - получить список названий и типов полей таблицы;\n"
                       f"🔹 &lt;<i>название таблицы</i>&gt; &lt;<i>название поля</i>&gt; &lt;<i>значение поля</i>&gt; - "
                       f"получить список найденных записей.")

DEL_CHAT_REFERENCE = (f"<b>Формат: /{Commands.DEL_CHAT.value} [option] ...</b>\n\n"
                      f"- Команда предназначена для удаления чата, вместе со связанным пользователем или группой.\n\n"
                      f"<b>Список опций:</b>\n"
                      f"🔹 &lt;<i>email чата</i>&gt; - удалить чат из базы данных.")

ADD_NOTIFY_SUBSCRIBER_REFERENCE = (f"<b>Формат: /{Commands.ADD_NOTIFY_SUBSCRIBER.value} [option] ...</b>\n\n"
                                   f"- Команда предназначена для подписки чата на заданный тип уведомлений.\n\n"
                                   f"<b>Список опций:</b>\n"
                                   "🔹 '<i>-list</i>' - получить список всех типов уведомлений для подписки;\n"
                                   "🔹 &lt;<i>название типа уведомления</i>&gt; '<i>-desc</i>' - "
                                   "получить описание типа уведомления;\n"
                                   "🔹 &lt;<i>email чата</i>&gt; &lt;<i>название типа уведомления</i>&gt; - "
                                   "подписать чат на выбранный тип уведомлений.")

DEL_NOTIFY_SUBSCRIBER_REFERENCE = (f"<b>Формат: /{Commands.DEL_NOTIFY_SUBSCRIBER.value} [option] ...</b>\n\n"
                                   f"- Команда предназначена для отзыва подписки у чата на заданный тип уведомлений.\n\n"
                                   f"<b>Список опций:</b>\n"
                                   "🔹 '<i>-list</i>' - получить список всех типов уведомлений для подписки;\n"
                                   "🔹 &lt;<i>название типа уведомления</i>&gt; '<i>-desc</i>' - "
                                   "получить описание типа уведомления;\n"
                                   "🔹 &lt;<i>email чата</i>&gt; &lt;<i>название типа уведомления</i>&gt; - "
                                   "отписать чат от выбранного типа уведомлений.")
