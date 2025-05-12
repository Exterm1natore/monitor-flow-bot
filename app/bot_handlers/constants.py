from enum import Enum


class Commands(Enum):
    START = "start"
    HELP = "help"
    MAN = "man"
    REGISTER = "register"
    SIGN_OUT = "sign_out"
    STOP = "stop"
    STATUS = "status"
    NOTIFY_ON = "notify_on"
    NOTIFY_OFF = "notify_off"


INFO_REQUEST_MESSAGE = ("❗️ Чтобы получить более подробную информацию о работе со мной и список доступных возможностей, "
                        f"отправьте мне команду <i>/{Commands.HELP.value}</i>.")
