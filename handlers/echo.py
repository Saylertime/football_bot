from aiogram import Router
from aiogram.types import Message

router_echo = Router()


@router_echo.message()
async def echo_handler(message: Message) -> None:
    # await message.answer(f'Повторяю: <b>{message.text}</b>')
    pass