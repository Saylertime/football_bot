from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.enums.chat_type import ChatType

from loader import bot
from keyboards.reply.create_markup import create_markup
from pg_maker import create_schema, add_chat


router_new_chat = Router()


@router_new_chat.message(Command("new_chat"))
async def all_games_func(message):
    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        await add_chat(message.chat.title or "", str(message.chat.id))

    msg = str(message.chat.title) + " " + str(message.chat.id)
    await bot.send_message(chat_id=68086662, text=msg)
