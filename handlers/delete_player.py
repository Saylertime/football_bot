from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from handlers.start import command_start_handler
from keyboards.reply.create_markup import create_markup
from states.overall import OverallState
from pg_maker import all_players, delete_player


router_delete_player = Router()


@router_delete_player.message(Command("delete_player"))
@router_delete_player.callback_query(F.data == "delete_player")
async def delete_player_func(message):
    if isinstance(message, CallbackQuery):
        message = message.message

    players = await all_players()
    buttons = [(name["name"], f"delete__{name['name']}") for name in players]
    buttons.append(("↩️ Назад в меню", "start"))
    markup = create_markup(buttons, columns=3)
    try:
        await message.edit_text("Кого кикаем?", reply_markup=markup)
    except:
        await message.answer("Кого кикаем?", reply_markup=markup)

@router_delete_player.callback_query(F.data.startswith("delete__"))
async def change_salary(callback):
    name = callback.data.split("__")[1]
    await delete_player(name)
    await callback.message.answer(f"Порощаемся с {name}...")
    await command_start_handler(callback)
