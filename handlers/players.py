from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from keyboards.reply.create_markup import create_markup
from states.overall import OverallState
from pg_maker import all_players, my_general_stats


router_players = Router()
buttons_back = [
    ("↩️ Назад в меню", "start"),
]


@router_players.message(Command("players"))
@router_players.callback_query(F.data == "players")
async def players_func(message):
    if isinstance(message, CallbackQuery):
        message = message.message

    buttons = [
        ("👤 Добавить игрока в базу", "new_player"),
        ("👉🏻🗑️ Удалить игрока", "delete_player"),
        ("👥Все игроки", "all_players"),
    ]
    buttons.extend(buttons_back)
    markup = create_markup(buttons)
    await message.edit_text("Игроки", reply_markup=markup)
