import asyncio
import uvicorn
from uvicorn import Config
import threading
from fastapi import FastAPI
from . import webhooks
from app.core.environment import API_HOST, API_PORT

# Настройка FastAPI
title = "Zabbix Webhook Handler"
desc = "Processes the received data from Zabbix and sends chat to notification subscribers."
app = FastAPI(debug=False, title=title, description=desc)

# Подключаем хуки
app.include_router(webhooks.router)


def run_zabbix_webhook_handler_server():
    """ Запустить сервер FastAPI на второстепенном потоке. """
    config = Config(app=app, host=API_HOST, port=API_PORT)

    server_thread = threading.Thread(target=run_server, name="ZabbixListener", args=[config], daemon=True)
    server_thread.start()


def run_server(config: Config):
    """
    Запуск сервера.

    :param config: Конфигурация сервера.
    """
    server = uvicorn.Server(config=config)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(server.serve())
