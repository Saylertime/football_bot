import asyncio
import os

from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from config_data import config
from handlers import routers
from loader import bot, dp
from middlewares.logging_middleware import LoggingMiddleware


LOCAL_ENV = config.LOCAL_ENV
WEBHOOK_URL = config.WEBHOOK_URL
ROUTE_FOR_WEBHOOK = config.ROUTE_FOR_WEBHOOK
PORT = int(config.PORT)
BOT_TOKEN = config.BOT_TOKEN
HOST = "0.0.0.0"


async def set_commands():
    commands = [
        BotCommand(command=cmd, description=desc)
        for cmd, desc in config.DEFAULT_COMMANDS
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


def routers_and_middleware():
    for router in routers:
        dp.include_router(router)
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())


async def on_startup() -> None:
    await set_commands()
    await bot.set_webhook(f"{WEBHOOK_URL}{ROUTE_FOR_WEBHOOK}")
    await bot.send_message(chat_id=68086662, text="Бот запущен на вебхуках!")


async def on_shutdown() -> None:
    await bot.send_message(chat_id=68086662, text="Бот остановлен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.session.close()


def main_webhook() -> None:
    routers_and_middleware()
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=ROUTE_FOR_WEBHOOK)
    setup_application(app, dp, bot=bot)

    loop = asyncio.new_event_loop()
    web.run_app(app, host=HOST, port=PORT, loop=loop)


async def main():
    await set_commands()
    routers_and_middleware()

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.send_message(chat_id=68086662, text="Бот запущен локально!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    if LOCAL_ENV == "local":
        asyncio.run(main())
    else:
        main_webhook()
