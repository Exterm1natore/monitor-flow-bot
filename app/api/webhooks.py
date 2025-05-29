from typing import Dict
from fastapi.responses import PlainTextResponse
from fastapi import Request, APIRouter
from app.core.environment import ENDPOINT_ZABBIX_WEBHOOKS
from app.core.bot_setup import app
from app import bot_handlers
from app.utils import json_format
router = APIRouter()


@router.post(f"{ENDPOINT_ZABBIX_WEBHOOKS}")
async def handle_webhook(request: Request):

    data: Dict = await request.json()

    notification_text = f"❗️Уведомление от Zabbix:\n\n{json_format.format_json_to_str(data)}"

    # Если нет необходимого поля
    bot_handlers.send_notification_to_subscribers(app, bot_handlers.NotificationTypes.ZABBIX, notification_text)

    return PlainTextResponse("✅ Webhook received", status_code=200)
