from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from keyboards.reply.create_markup import create_markup
from states.overall import OverallState
from pg_maker import add_player


router_new_player = Router()


@router_new_player.message(Command("new_player"))
@router_new_player.callback_query(F.data == "new_player")
async def new_player(message, state):
    if isinstance(message, CallbackQuery):
        message = message.message

    await message.edit_text(
        "Введи имя и ник автора через запятую с пробелом. БЕЗ @. Пример: \n\n"
        "Алексей Глинкин, saylertime"
    )
    await state.set_state(OverallState.new_player)


@router_new_player.message(OverallState.new_player)
async def add_player_to_db(message, state):
    try:
        name, username = message.text.split(", ")
        await add_player(name, username)
        buttons = [
            ("👤 Добавить ещё одного", "new_player"),
            ("👥 Посмотреть всех игроков", "all_players"),
            ("↩️ Назад в меню", "start"),
        ]
        markup = create_markup(buttons)

        await message.answer(f"{name} добавлен!\n\n", reply_markup=markup)
    except:
        buttons = [
            ("Добавить игрока", "new_player"),
            ("Назад в меню", "start"),
        ]
        markup = create_markup(buttons)
        await message.answer(f"Что-то не получилось", reply_markup=markup)
    await state.clear()
