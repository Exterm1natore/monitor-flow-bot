from fastapi.testclient import TestClient
from unittest.mock import patch

from app.api.base import app
from app.core.bot_setup import app as bot_app
from app.core.environment import WEBHOOK_EVENT_ENDPOINT


client = TestClient(app)


@patch("app.bot_handlers.send_notification_to_subscribers")
def test_handle_webhook_success(mock_send):
    payload = {
        "trigger": "CPU load is high",
        "host": "server1",
        "value": "80%"
    }

    response = client.post(WEBHOOK_EVENT_ENDPOINT, json=payload)

    assert response.status_code == 200
    assert response.text == "✅ Webhook received"

    # Проверяем, что send_notification_to_subscribers был вызван
    mock_send.assert_called_once()

    args = mock_send.call_args[0]
    assert args[0] is bot_app
    assert args[1].name == "ZABBIX"
    assert "CPU load is high" in args[2]
    assert "server1" in args[2]
