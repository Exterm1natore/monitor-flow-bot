import inspect
from typing import get_type_hints
from functools import wraps
import logging
from bot.bot import Bot, Event


# -------------------- Декораторы --------------------


def group_administrator_access(func):
    """
    Проверить и выполнить функцию только в случае, если запрос делает администратор группы.
    """
    sig = inspect.signature(func)
    params = list(sig.parameters.values())

    if len(params) < 2:
        raise TypeError(f"❌ The function '{func.__name__}' must take at least two arguments: bot and event.")

    # Получаем аннотации типов
    type_hints = get_type_hints(func)

    first_param_type = type_hints.get(params[0].name)
    second_param_type = type_hints.get(params[1].name)

    # Проверяем соответствие типам
    if first_param_type is not Bot or second_param_type is not Event:
        raise TypeError(
            f"❌ The first two parameters of the function '{func.__name__}' must have types Bot and Event respectively.\n"
            f"Detected: {first_param_type} and {second_param_type}"
        )

    @wraps(func)
    def wrapper(bot: Bot, event: Event, *args, **kwargs):
        # Блок проверки списка администраторов
        try:
            response = bot.get_chat_admins(event.from_chat)
            response.raise_for_status()

            response_data = response.json()

            # Если ответ за запрос списка администраторов корректен
            if response_data.get('ok', False):
                is_admin = any(user['userId'] == event.message_author['userId'] for user in response_data.get('admins', []))
                'admins'
                if not is_admin:
                    raise PermissionError("⛔️ <b>Нет доступа для выполнения команды.</b>\n"
                                          "Вы не администратор группы.")
            else:
                error_text = "❌ <b>Нет возможности выполнить команду.</b>"

                desc_error: str = response_data.get('description', "")

                if "permission denied" in desc_error.lower():
                    error_text += ("\nБот не обладает правами администратора данной группы, "
                                   "для выполнения заданного действия.")
                else:
                    error_text += f"\nПричина: {desc_error}"

                raise PermissionError(error_text)
        except PermissionError as permission_error:
            bot.send_text(event.from_chat, str(permission_error), reply_msg_id=event.msgId, parse_mode='HTML')
            return
        except Exception as other_error:
            error_text = "❌ <b>Нет возможности выполнить команду.</b>"
            error_text += f"\nПричина: {str(other_error)}"
            logging.getLogger(__name__).exception(error_text)
            bot.send_text(event.from_chat, error_text, reply_msg_id=event.msgId, parse_mode='HTML')
            return

        return func(bot, event, *args, **kwargs)
    return wrapper
