from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from keyboards.reply.create_markup import create_markup
from states.overall import OverallState
from pg_maker import (
    all_my_games, all_games,
    results_of_the_game, find_player_id,
    my_stats_in_match, my_general_stats, get_all_player_totals_goals,
    get_all_player_totals_assists, get_all_player_totals_goals_and_assists
)


router_general_stats = Router()


@router_general_stats.message(Command("general_stats"))
@router_general_stats.callback_query(F.data.startswith("general_stats_"))
async def general_stats_func(event):
    # Если пришёл CallbackQuery
    if isinstance(event, CallbackQuery):
        data = event.data  # <-- вот так получаем data
        message = event.message
    else:
        data = None
        message = event  # Это Message

    if data == "general_stats_goal":
        results = await get_all_player_totals_goals()
        msg = "* ТАБЛИЦА ЛУЧШИХ ПО ГОЛАМ *\n\n"
    elif data == "general_stats_assist":
        results = await get_all_player_totals_assists()
        msg = "* ТАБЛИЦА ЛУЧШИХ ПО АССИСТАМ*\n\n"
    elif data == "general_stats_goal_and_assist":
        results = await get_all_player_totals_goals_and_assists()
        msg = "* ТАБЛИЦА ЛУЧШИХ ПО ГОЛ + ПАС*\n\n"



    for num, player in enumerate(results, 1):
        msg += (f"* {num}. {player['name']} *  — @{player['username']}\n"
                f"⚽ Голы: {player['total_goals']}\n"
                f"🤝 Ассисты: {player['total_assists']}\n")

        if player['total_autogoals'] > 0:
            msg += f"🤡 Автоголы: {player['total_autogoals']}\n"
        msg += "______________ \n"

    buttons_back = [
        ("↩️ Назад в меню", "start"),
    ]
    markup = create_markup(buttons_back)
    await message.edit_text(msg, reply_markup=markup, parse_mode="Markdown")
