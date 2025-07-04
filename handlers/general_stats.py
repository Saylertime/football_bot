from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from keyboards.reply.create_markup import create_markup
from states.overall import OverallState
from pg_maker import (
    all_my_games, all_games,
    results_of_the_game, find_player_id,
    my_stats_in_match, my_general_stats, get_all_player_totals
)


router_general_stats = Router()


@router_general_stats.message(Command("general_stats"))
@router_general_stats.callback_query(F.data == "general_stats")
async def general_stats_func(message):
    if isinstance(message, CallbackQuery):
        message = message.message

    results = await get_all_player_totals()
    msg = "* ТАБЛИЦА ЛУЧШИХ *\n\n"

    for num, player in enumerate(results, 1):
        msg += (f"* {num}. {player['name']} *  — @{player['username']}\n"
                f"⚽ Голы: {player['total_goals']}\n"
                f"🤝 Ассисты: {player['total_assists']}\n"
                f"______________ \n")

    buttons_back = [
        ("↩️ Назад в меню", "start"),
    ]
    markup = create_markup(buttons_back)
    await message.edit_text(msg, reply_markup=markup, parse_mode="Markdown")
