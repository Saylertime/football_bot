from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from keyboards.reply.create_markup import create_markup
from states.overall import OverallState
from pg_maker import (all_games, find_players_without_game, find_players_in_game,
                      register_player_in_game, unregister_player_from_game,
                      add_goal, add_assist, results_of_the_game, delete_game)


router_all_games = Router()

MONTHS_GENITIVE = {
    1: "января",  2: "февраля", 3: "марта",    4: "апреля",
    5: "мая",     6: "июня",    7: "июля",     8: "августа",
    9: "сентября",10: "октября",11: "ноября",   12: "декабря",
}


@router_all_games.message(Command("all_games"))
@router_all_games.callback_query(F.data == "all_games")
async def all_games_func(message, state):
    if isinstance(message, CallbackQuery):
        message = message.message

    games = await all_games()
    buttons = []
    for game in games:
        dt = game["played_at"]
        label = f"{dt.day:02d} {MONTHS_GENITIVE[dt.month]} {dt.year}"
        buttons.append((label, f"games__{game['id']}"))
    buttons.append(("↩️ Назад в меню", "start"))
    markup = create_markup(buttons, columns=3)
    await message.edit_text("Все игры", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("games__"))
async def one_game(callback):
    game_id = callback.data.split("__")[1]
    buttons = [
        ("🆕 Добавить игрока", f"insert_player__{game_id}"),
        ("❌ Убрать игрока", f"remove_player__{game_id}"),
        ("⚽ Гол", f"add_goal__{game_id}"),
        ("🤝 Ассист", f"add_assist__{game_id}"),
        ("📊 Статистика", f"results__{game_id}"),
        ("🗑️ Удалить игру", f"game_delete__{game_id}"),
        ("↩️ Назад в меню", "start"),
    ]
    markup = create_markup(buttons, columns=2)
    await callback.message.edit_text("Что делаем?", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("insert_player__"))
async def insert_player_func(callback):
    game_id = callback.data.split("__")[1]
    players_without_game = await find_players_without_game(int(game_id))
    buttons = [
        (player["name"], f"add__{str(player['id'])}__{game_id}") for player in players_without_game
    ]
    markup = create_markup(buttons, columns=2)
    await callback.message.edit_text("Игроки, которых еще нет в этой игре:", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("add__"))
async def add_player_func(callback):
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    await register_player_in_game(game_id, player_id)
    await callback.message.answer("Игрок добавлен в игру")
    await all_games_func(callback)


@router_all_games.callback_query(F.data.startswith("remove_player__"))
async def remove_player_func(callback):
    game_id = callback.data.split("__")[1]
    players_in_game = await find_players_in_game(int(game_id))
    buttons = [
        (player["name"], f"remove__{str(player['id'])}__{game_id}") for player in players_in_game
    ]
    markup = create_markup(buttons, columns=2)
    await callback.message.edit_text("Игроки, которые зареганы на игру:", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("remove__"))
async def delete_player_func(callback):
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    await unregister_player_from_game(game_id, player_id)
    await callback.message.answer("Игрок удален из игры")
    await all_games_func(callback)


@router_all_games.callback_query(F.data.startswith("add_goal__"))
async def add_goal_func(callback):
    game_id = int(callback.data.split("__")[1])
    players_in_game = await find_players_in_game(int(game_id))
    buttons = [
        (player["name"], f"goal__{str(player['id'])}__{game_id}") for player in players_in_game
    ]
    markup = create_markup(buttons, columns=2)
    await callback.message.edit_text("Кто забил?", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("goal__"))
async def goal_func(callback):
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    await add_goal(game_id, player_id)
    await callback.message.answer("Красиво делает!")
    await all_games_func(callback)


@router_all_games.callback_query(F.data.startswith("add_assist__"))
async def add_assist_func(callback):
    game_id = int(callback.data.split("__")[1])
    players_in_game = await find_players_in_game(int(game_id))
    buttons = [
        (player["name"], f"assist__{str(player['id'])}__{game_id}") for player in players_in_game
    ]
    markup = create_markup(buttons, columns=2)
    await callback.message.answer("Кто сделал ассист?", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("assist__"))
async def assist_func(callback):
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    await add_assist(game_id, player_id)
    await callback.message.answer("Красиво раздаёт пасы!")
    await all_games_func(callback)


@router_all_games.callback_query(F.data.startswith("results__"))
async def results_func(callback):
    game_id = int(callback.data.split("__")[1])
    msg = await results_of_the_game(game_id)
    buttons = [
        ("⬅️ Назад в игры", "all_games"),
        ("↩️ Назад в меню", "start")
    ]
    markup = create_markup(buttons)
    await callback.message.edit_text(msg, reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("game_delete__"))
async def delete_game_func(callback, state):
    game_id = int(callback.data.split("__")[1])
    await delete_game(game_id)
    await callback.message.answer("Игра удалена")
    await all_games_func(callback, state)
