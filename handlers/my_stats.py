from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from keyboards.reply.create_markup import create_markup
from states.overall import OverallState
from utils.calend import MONTHS_GENITIVE
from pg_maker import (
    all_my_games, all_games,
    results_of_the_game, find_player_id,
    my_stats_in_match, my_general_stats
)


router_my_stats = Router()

buttons_back = [
    ("⬅️ Назад в статистику", "my_stats"),
    ("↩️ Назад в меню", "start"),
]


@router_my_stats.message(Command("stats"))
@router_my_stats.callback_query(F.data == "stats")
async def stats_func(message):
    if isinstance(message, CallbackQuery):
        message = message.message

    buttons = [
        ("📊 Моя статистика", "my_stats"),
        ("🌐 Общая стата за всё время", "general_stats"),
    ]
    markup = create_markup(buttons)
    await message.edit_text("Что смотрим?", reply_markup=markup)


@router_my_stats.callback_query(F.data.startswith("my_stats"))
async def my_stats_func(callback):
    buttons = [
        ("📈 Стата за матч", "match_stats"),
        ("🌐 Стата за всё время", "all_time_stats"),
        ("↩️ Назад в меню", "start"),
    ]
    markup = create_markup(buttons)
    await callback.message.edit_text("Что смотрим?", reply_markup=markup)


@router_my_stats.callback_query(F.data.startswith("match_stats"))
async def match_stats_func(callback):
    user = callback.from_user
    message = callback.message
    player_id = await find_player_id(user.username)
    games = await all_my_games(player_id)

    buttons = []
    for game in games:
        dt = game["played_at"]
        label = f"{dt.day:02d} {MONTHS_GENITIVE[dt.month]} {dt.year}"
        buttons.append((label, f"my_games__{game['id']}"))
    buttons.extend([
        ("⬅️ Назад в статистику", "my_stats"),
        ("↩️ Назад в меню", "start"),
    ])
    markup = create_markup(buttons, columns=2)
    await message.edit_text("Все игры", reply_markup=markup)


@router_my_stats.callback_query(F.data.startswith("my_games__"))
async def me_games_func(callback):
    user = callback.from_user
    message = callback.message
    game_id = int(callback.data.split("__")[1])
    player_id = await find_player_id(user.username)
    stats = await my_stats_in_match(player_id, game_id)
    if not stats:
        await callback.message.answer("Нет статистики для этого матча.")
        return
    msg = (
        f"⚽ Голы: {stats['goals']}\n"
        f"🤝 Ассисты: {stats['assists']}\n"
    )
    if stats["autogoals"]:
        msg += f"🤡 Автоголы: {stats['autogoals']}"
    markup = create_markup(buttons_back)
    await message.edit_text(msg, reply_markup=markup, parse_mode="Markdown")


@router_my_stats.callback_query(F.data.startswith("all_time_stats"))
async def all_time_stats_func(callback):
    user = callback.from_user
    player_id = await find_player_id(user.username)
    message = callback.message
    my_stats = await my_general_stats(player_id)
    if my_stats["matches_played"] == 0:
        msg = "🔸 У тебя ещё нет сыгранных матчей"
    else:
        msg = (
            "📊 *Твоя статистика*\n\n\n"
            f"🥅 Сыграно матчей: {my_stats['matches_played']}\n"
            f"⚽ Забито голов: {my_stats['total_goals']}\n"
            f"🤝 Сделано ассистов: {my_stats['total_assists']}"
        )
    markup = create_markup(buttons_back)
    await message.edit_text(msg, reply_markup=markup, parse_mode="Markdown")

