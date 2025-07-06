from aiogram import Router, F
from aiogram import types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.reply.create_markup import create_markup
from states.overall import OverallState
from pg_maker import all_players, change_players_name, my_general_stats


router_all_players = Router()

buttons_back = [
    ("⬅️ Назад к игрокам", "players"),
    ("↩️ Назад в меню", "start"),
]


@router_all_players.message(Command("all_players"))
@router_all_players.callback_query(F.data == "all_players")
async def all_players_func(message):
    if isinstance(message, CallbackQuery):
        message = message.message

    players = await all_players()
    buttons = [(name["name"], f"players__{name['username']}__{name['id']}__{name['name']}") for name in players]
    buttons.extend(buttons_back)
    markup = create_markup(buttons, columns=3)
    try:
        await message.edit_text("Все игроки", reply_markup=markup)
    except:
        await message.answer("Все игроки", reply_markup=markup)


@router_all_players.callback_query(F.data.startswith("players__"))
async def player_func(callback):
    username = callback.data.split("__")[1]
    player_id = callback.data.split("__")[2]
    name = callback.data.split("__")[3]
    buttons = [
        ("📈 Посмотреть стату", f"see_stats__{player_id}__{name}"),
        ("⚙️ Изменить имя", f"change_name__{player_id}__{name}"),
        ("🗑 Удалить из базы", f"delete__{name}"),
        ]
    buttons.extend(buttons_back)
    markup = create_markup(buttons)
    await callback.message.edit_text("Что делаем?", reply_markup=markup)


@router_all_players.callback_query(F.data.startswith("see_stats"))
async def see_stats_func(callback):
    player_id = int(callback.data.split("__")[1])
    name = callback.data.split("__")[2]
    message = callback.message
    his_stats = await my_general_stats(player_id)
    if his_stats["matches_played"] == 0:
        msg = "🔸 У тебя ещё нет сыгранных матчей"
    else:
        msg = (
            f"📊 *Статистика {name}*\n\n\n"
            f"🥅 Сыграно матчей: {his_stats['matches_played']}\n"
            f"⚽ Забито голов: {his_stats['total_goals']}\n"
            f"🤝 Сделано ассистов: {his_stats['total_assists']}"
        )
    markup = create_markup(buttons_back)
    await message.edit_text(msg, reply_markup=markup, parse_mode="Markdown")


@router_all_players.callback_query(F.data.startswith("change_name"))
async def change_name_func(callback, state):
    player_id = int(callback.data.split("__")[1])
    await state.update_data(player_id=player_id)
    await callback.message.edit_text("Введи новое имя")
    await state.set_state(OverallState.change_name)


@router_all_players.message(OverallState.change_name)
async def changed_name_func(message, state):
    new_name = message.text.strip()

    data = await state.get_data()
    player_id = data.get("player_id")
    if player_id is None:
        await message.answer("❗ Что-то пошло не так, попробуй ещё раз.")
        return

    await change_players_name(new_name, player_id)
    await message.answer(f"✅ Имя изменено на «{new_name}».")
    await state.clear()
