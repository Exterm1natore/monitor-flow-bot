from typing import List, Optional
from requests import Response
import time
import logging
from bot.bot import Bot
from bot.constant import ChatType
from app.utils import text_format
from app.core import executor_pool
from tenacity import retry, stop_after_attempt, wait_exponential, RetryError
from ratelimiter import RateLimiter
from pybreaker import CircuitBreaker, CircuitBreakerError


class MessageDeliveryError(Exception):
    """
    Ошибка доставки сообщения до адресата.
    """

    def __init__(self, chat_id: str, description: str, response_data: dict, original_exception: Exception = None):
        super().__init__(f"❌ Message delivery failed to {chat_id}: {description}")
        self.chat_id = chat_id
        self.description = description
        self.response_data = response_data
        self.original_exception = original_exception

    def __repr__(self):
        return (
            f"<MessageDeliveryError chat_id={self.chat_id!r} "
            f"description={self.description!r} "
            f"response_data={self.response_data!r} "
            f"original_exception={self.original_exception!r}>"
        )


def send_text_or_raise(bot: Bot, chat_id: str, text: str, reply_msg_id=None, forward_chat_id=None, forward_msg_id=None,
                       inline_keyboard_markup=None, parse_mode=None, format_=None) -> Response:
    """
    Отправить сообщение в чат через бот.
    При HTTP-ошибке или ошибке доставки до адресата выбрасывается исключение.

    :param bot: Объект Bot VKTeams.
    :param chat_id: ID чата.
    :param text: Текст сообщения.
    :param reply_msg_id: ID сообщения, на которое создаётся ответ.
    :param forward_chat_id: ID чата, куда пересылается сообщение (передаётся только с id пересылаемого сообщения).
    :param forward_msg_id: ID пересылаемого сообщения (передаётся только с id чата, куда пересылается сообщение).
    :param inline_keyboard_markup: Встроенная в сообщение клавиатура.
    :param parse_mode: Формат разбора текста.
    :param format_: Описание форматирования текста.
    :return: Объект Response, содержащий ответ сервера на HTTP-запрос.
    :raises requests.HTTPError: Ответ сервера содержит HTTP-ошибку.
    :raises MessageDeliveryError: Ошибка доставки сообщения до адресата.
    """
    response = bot.send_text(
        chat_id=chat_id,
        text=text,
        reply_msg_id=reply_msg_id,
        forward_chat_id=forward_chat_id,
        forward_msg_id=forward_msg_id,
        inline_keyboard_markup=inline_keyboard_markup,
        parse_mode=parse_mode,
        format_=format_
    )

    # Выбрасываем исключение при ошибочном статусе
    response.raise_for_status()
    # Тело ответа сервера
    data: dict = response.json()
    # Если ошибка отправки, создаём исключение
    if not data.get('ok'):
        raise MessageDeliveryError(
            chat_id=chat_id,
            description=data.get("description", "(no description)"),
            response_data=data
        )

    return response


def edit_text_or_raise(bot: Bot, chat_id: str, msg_id: str, text: str, inline_keyboard_markup=None,
                       parse_mode=None, format_=None) -> Response:
    """
    Изменить сообщение через бот.
    **Можно изменить только сообщение бота.**
    При HTTP-ошибке или ошибке доставки до адресата выбрасывается исключение.

    :param bot: Объект Bot VKTeams.
    :param chat_id: ID чата.
    :param msg_id: ID сообщения, которое изменяется.
    :param text: Текст сообщения.
    :param inline_keyboard_markup: Встроенная в сообщение клавиатура.
    :param parse_mode: Формат разбора текста.
    :param format_: Описание форматирования текста.
    :return: Объект Response, содержащий ответ сервера на HTTP-запрос.
    :raises requests.HTTPError: Ответ сервера содержит HTTP-ошибку.
    :raises MessageDeliveryError: Ошибка доставки сообщения до адресата.
    """
    response = bot.edit_text(
        chat_id=chat_id,
        msg_id=msg_id,
        text=text,
        inline_keyboard_markup=inline_keyboard_markup,
        parse_mode=parse_mode,
        format_=format_
    )

    # Выбрасываем исключение при ошибочном статусе
    response.raise_for_status()
    # Тело ответа сервера
    data: dict = response.json()
    # Если ошибка отправки, создаём исключение
    if not data.get('ok'):
        raise MessageDeliveryError(
            chat_id=chat_id,
            description=data.get("description", "(no description)"),
            response_data=data
        )

    return response


def send_long_text(bot: Bot, chat_id: str, text: str, max_len_text: int = 4096, reply_msg_id=None,
                   inline_keyboard_markup=None, parse_mode=None, format_=None) -> Response:
    """
    Отправить длинное сообщение (разбивает на части, если превышает max_len_text).
    
    :param bot: Объект Bot VKTeams.
    :param chat_id: ID чата.
    :param text: Текст сообщения.
    :param max_len_text: Максимальная длинна текста для одного сообщения.
    :param reply_msg_id: ID сообщения, на которое создаётся ответ.
    :param inline_keyboard_markup: Встроенная в сообщение клавиатура (добавляется к последнему сообщению).
    :param parse_mode: Формат разбора текста.
    :param format_: Описание форматирования текста.
    :return: Объект Response, содержащий ответ сервера на HTTP-запрос последнего сообщения.
    :raises requests.HTTPError: Ответ сервера содержит HTTP-ошибку.
    :raises MessageDeliveryError: Ошибка доставки сообщения до адресата.
    :raises
    """
    parts = text_format.split_text(text, max_len_text)

    # Если количество частей превышает 50, отправить ошибку
    if len(parts) > 50:
        raise ValueError("❌ The text is too long.")

    # Получаем тип чата, если доступно
    response = bot.get_chat_info(chat_id)
    chat_type: Optional[str] = None
    if response.ok:
        chat_type = response.json().get('type', None)

    for i, part in enumerate(parts[:-1], start=1):
        send_text_or_raise(
            bot=bot,
            chat_id=chat_id,
            text=part,
            reply_msg_id=reply_msg_id,
            inline_keyboard_markup=None,
            parse_mode=parse_mode,
            format_=format_
        )
        # Если приватный тип чата, то делаем задержку 1 секунду после 30 сообщений
        if chat_type == ChatType.PRIVATE.value:
            if i % 29 == 0:
                time.sleep(1)
        else:
            time.sleep(1)

    return send_text_or_raise(
        bot=bot,
        chat_id=chat_id,
        text=parts[-1],
        reply_msg_id=reply_msg_id,
        inline_keyboard_markup=inline_keyboard_markup,
        parse_mode=parse_mode,
        format_=format_
    )


def broadcast_to_chats(
    *,
    bot,
    chat_ids: List[str],
    text: str,
    inline_keyboard_markup=None,
    parse_mode: Optional[str] = None,
    format_=None,
    wait_for_completion: bool = False,
    logger: Optional[logging.Logger] = None,
    suppress_notification_log: bool = False,
    rate_limiter: RateLimiter = RateLimiter(max_calls=15, period=1),
    breaker: CircuitBreaker = CircuitBreaker(fail_max=5, reset_timeout=60)
) -> None:
    """
    Отправить сообщение в заданный список чатов.
    Используется многопоточность.
    Учитывается очередь отправки в секунду.
    При заданном количестве ошибок подряд, отправки приостановится на заданный промежуток времени.

    :param bot: Объект Bot VKTeams.
    :param chat_ids: Список ID чатов, в которые направляется сообщение.
    :param text: Отправляемое сообщение.
    :param inline_keyboard_markup: Встроенная клавиатура.
    :param parse_mode: Тип разбора текста.
    :param format_: Формат текста (передаётся раздельно с parse_mod).
    :param wait_for_completion: Ожидать ли завершения отправки всех сообщений.
    :param logger: Внешний логгер.
    :param suppress_notification_log: Подавлять ли ошибки отправки сообщений.
    :param rate_limiter: Количество сообщений за период секунд.
    :param breaker: Остановка после количества ошибок подряд и время восстановления.
    """
    logger = logger or logging.getLogger(__name__)

    def _do_send(chat_id: str):
        """Фактический вызов API."""
        send_long_text(
            bot=bot,
            chat_id=chat_id,
            text=text,
            reply_msg_id=None,
            inline_keyboard_markup=inline_keyboard_markup,
            parse_mode=parse_mode,
            format_=format_
        )

    # оборачиваем в retry + rate limiter + circuit breaker
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    def _protected_send(chat_id: str):
        # rate limit
        with rate_limiter:
            # circuit breaker
            return breaker.call(_do_send, chat_id)

    def safe_send(chat_id: str):
        try:
            _protected_send(chat_id)
        except CircuitBreakerError as cb_err:
            logger.error(f"⚠️ Circuit open, skipping chat {chat_id}: {cb_err}")
        except RetryError as retry_err:
            logger.error(f"❌ Retry failed for chat {chat_id}: {retry_err}")
        except MessageDeliveryError as delivery_err:
            if not suppress_notification_log:
                logger.error(delivery_err)
        except Exception as e:
            err_message = f"❌ Unexpected error sending to {chat_id}: {e}"
            if not suppress_notification_log:
                logger.exception(err_message)

    executor = executor_pool.get_executor()

    futures = []
    for cid in chat_ids:
        future = executor.submit(safe_send, cid)
        futures.append(future)

    if wait_for_completion:
        # Ждём завершения всех задач
        for future in futures:
            future.result()
