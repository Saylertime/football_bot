from aiogram.dispatcher.middlewares.base import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from utils.logger import logger


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        try:
            if isinstance(event, Message):
                username = (
                    f"@{event.from_user.username}"
                    if event.from_user.username
                    else f"ID: {event.from_user.id}"
                )
                logger.warning(f"{username}: команда {event.text}")
            elif isinstance(event, CallbackQuery):
                username = (
                    f"@{event.from_user.username}"
                    if event.from_user.username
                    else f"ID: {event.from_user.id}"
                )
                logger.warning(f"{username}: callback {event.data}")
        except Exception as e:
            logger.error(f"Error in LoggingMiddleware: {e}")
        return await handler(event, data)
