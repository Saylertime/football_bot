import aiofiles
from aiogram import Router, F
from aiogram.types import Message

router_echo = Router()


@router_echo.message(F.text.lower() == "история")
async def history_log(message):
    async with aiofiles.open("bot.log", mode="r") as file:
        lines = await file.readlines()
        filtered_lines = [
            line for line in lines if "@" in line and "история" not in line.lower()
        ]
        msg = "\n".join(filtered_lines[-30:])
        await message.answer(f"{msg}")


@router_echo.message()
async def echo_handler(message: Message) -> None:
    # await message.answer(f'Повторяю: <b>{message.text}</b>')
    pass