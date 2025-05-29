from typing import Dict
from fastapi.responses import PlainTextResponse
from fastapi import Request, APIRouter
from app.core.environment import WEBHOOK_EVENT_ENDPOINT
from app.core.bot_setup import app
from app import bot_handlers
from app.utils import json_format
router = APIRouter()


@router.post(f"{WEBHOOK_EVENT_ENDPOINT}")
async def handle_webhook(request: Request):
    """
    Принять webhook на заданную конечную точку,
    отформатировать тело запроса и отправить
    всем подписчикам уведомлений типа, относящегося к Zabbix.
    Webhook-и должны приходить от системы мониторинга Zabbix.
    Тело запроса должно содержать данные события, отправленные Zabbix.

    :param request: Запрос от Zabbix.
    """
    data: Dict = await request.json()

    notification_text = f"❗️Уведомление от Zabbix:\n\n{json_format.format_json_to_str(data)}"

    # Если нет необходимого поля
    bot_handlers.send_notification_to_subscribers(app, bot_handlers.NotificationTypes.ZABBIX, notification_text)

    return PlainTextResponse("✅ Webhook received", status_code=200)
