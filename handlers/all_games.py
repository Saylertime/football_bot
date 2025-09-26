from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from keyboards.reply.create_markup import create_markup
from states.overall import OverallState
from utils.calend import MONTHS_GENITIVE
from pg_maker import (all_games, find_players_without_game, find_players_in_game,
                      register_player_in_game, unregister_player_from_game,
                      add_goal, add_assist, add_autogoal, results_of_the_game,
                      delete_game, remove_goal, remove_assist, remove_autogoal,
                      find_players_with_something, add_points, add_overall_pts)


router_all_games = Router()


@router_all_games.message(Command("games"))
@router_all_games.callback_query(F.data == "games")
async def games_func(message, state):
    if isinstance(message, CallbackQuery):
        message = message.message
    buttons = [
        ("🎮 Новая игра", "add_game"),
        ("🍿 Все игры", "all_games"),
    ]
    markup = create_markup(buttons)
    await message.edit_text("Что делаем?", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("all_games"))
async def all_games_func(callback, state):
    games = await all_games()
    buttons = []
    for game in games:
        dt = game["played_at"]
        label = f"{dt.day:02d} {MONTHS_GENITIVE[dt.month]} {dt.year}"
        buttons.append((label, f"games__{game['id']}__{label}"))
    buttons.append(("↩️ Назад в меню", "start"))
    markup = create_markup(buttons, columns=3)
    await callback.message.edit_text("Все игры", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("games__"))
async def one_game(callback):
    game_id = callback.data.split("__")[1]
    played_at = callback.data.split("__")[2]
    buttons = [
        ("⚽ Гол", f"add_goal__{game_id}__{played_at}"),
        ("🤝 Ассист", f"add_assist__{game_id}__{played_at}"),
        ("🤡 Автогол", f"add_autogoal__{game_id}__{played_at}"),
        ("🚫⚽ Отменить голы", f"remove_goal__{game_id}__{played_at}"),
        ("🚫🤝 Отменить ассисты", f"remove_assist__{game_id}__{played_at}"),
        ("🚫🤡 Отменить автогол", f"remove_autogoal__{game_id}__{played_at}"),
        ("📊 Статистика", f"results__{game_id}__{played_at}"),
        ("🆕 Добавить игрока", f"insert_player__{game_id}__{played_at}"),
        ("❌ Убрать игрока", f"remove_player__{game_id}__{played_at}"),
        ("3️⃣ +3 очка игроку", f"point_player__{game_id}__{played_at}__3"),
        ("1️⃣ +1 очко игроку", f"point_player__{game_id}__{played_at}__1"),
        ("🔢 + PTS", f"more_points_player__{game_id}__{played_at}"),
        ("🗑️ Удалить игру", f"game_delete__{game_id}__{played_at}"),
        ("↩️ Назад в меню", "start"),
    ]
    markup = create_markup(buttons, columns=2)
    await callback.message.edit_text(f"Игра {played_at}", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("insert_player__"))
async def insert_player_func(callback):
    game_id = callback.data.split("__")[1]
    played_at = callback.data.split("__")[2]
    players_without_game = await find_players_without_game(int(game_id))
    buttons = [
        (player["name"], f"add__{str(player['id'])}__{game_id}__{played_at}") for player in players_without_game
    ]
    buttons.append(("↩️ Назад в игру", f"games__{game_id}__{played_at}"))
    markup = create_markup(buttons, columns=2)
    await callback.message.edit_text("Игроки, которых еще нет в этой игре:", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("add__"))
async def add_player_func(callback):
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    played_at = callback.data.split("__")[3]
    await register_player_in_game(game_id, player_id)
    buttons = [("↩️ Назад в игру", f"games__{game_id}__{played_at}")]
    markup = create_markup(buttons)
    await callback.message.edit_text("Игрок добавлен в игру", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("remove_player__"))
async def remove_player_func(callback):
    game_id = callback.data.split("__")[1]
    played_at = callback.data.split("__")[2]
    players_in_game = await find_players_in_game(int(game_id))
    buttons = [
        (player["name"], f"remove__{str(player['id'])}__{game_id}__{played_at}") for player in players_in_game
    ]
    markup = create_markup(buttons, columns=2)
    await callback.message.edit_text("Игроки, которые зареганы на игру:", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("remove__"))
async def delete_player_func(callback):
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    played_at = callback.data.split("__")[3]

    await unregister_player_from_game(game_id, player_id)
    buttons = [("↩️ Назад в игру", f"games__{game_id}__{played_at}")]
    markup = create_markup(buttons)
    await callback.message.edit_text("Игрок удалён из игры", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("add_goal__"))
async def add_goal_func(callback):
    game_id = int(callback.data.split("__")[1])
    played_at = callback.data.split("__")[2]
    players_in_game = await find_players_in_game(int(game_id))
    buttons = [
        (player["name"], f"goal__{str(player['id'])}__{game_id}__{played_at}") for player in players_in_game
    ]
    buttons.append(("↩️ Назад в игру", f"games__{game_id}__{played_at}"))
    markup = create_markup(buttons, columns=2)
    await callback.message.edit_text("Кто забил?", reply_markup=markup)


#################

@router_all_games.callback_query(F.data.startswith("goal__"))
async def goal_func(callback):
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    played_at = callback.data.split("__")[3]
    buttons = [(str(points), f"add_few_goals__{str(player_id)}__{game_id}__{played_at}__{str(points)}") for points in
               range(21)]
    markup = create_markup(buttons, 4)
    await callback.message.edit_text("Сколько наклепал за игру?", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("add_few_goals__"))
async def few_goals_func(callback):
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    played_at = callback.data.split("__")[3]
    points = int(callback.data.split("__")[4])
    await add_goal(game_id, player_id, points)
    buttons = [("↩️ Назад в игру", f"games__{game_id}__{played_at}")]
    markup = create_markup(buttons)
    await callback.message.edit_text("Красиво делает!", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("remove_goal__"))
async def remove_goal_func(callback):
    game_id = int(callback.data.split("__")[1])
    played_at = callback.data.split("__")[2]
    players_in_game = await find_players_with_something(int(game_id), something="goals")
    buttons = [
        (player["name"], f"ungoal__{str(player['id'])}__{game_id}__{played_at}") for player in players_in_game
    ]
    buttons.append(("↩️ Назад в игру", f"games__{game_id}__{played_at}"))
    markup = create_markup(buttons, columns=2)
    await callback.message.edit_text("Кого отменяем?", reply_markup=markup)

@router_all_games.callback_query(F.data.startswith("ungoal__"))
async def remove_goal_func(callback):
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    played_at = callback.data.split("__")[3]
    await remove_goal(game_id, player_id)
    buttons = [("↩️ Назад в игру", f"games__{game_id}__{played_at}")]
    markup = create_markup(buttons)
    await callback.message.edit_text("Галя, отмена", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("add_assist__"))
async def add_assist_func(callback):
    game_id = int(callback.data.split("__")[1])
    played_at = callback.data.split("__")[2]
    players_in_game = await find_players_in_game(int(game_id))
    buttons = [
        (player["name"], f"assist__{str(player['id'])}__{game_id}__{played_at}") for player in players_in_game
    ]
    buttons.append(("↩️ Назад в игру", f"games__{game_id}__{played_at}"))
    markup = create_markup(buttons, columns=2)
    await callback.message.edit_text("Кто сделал ассист?", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("assist__"))
async def assist_func(callback):
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    played_at = callback.data.split("__")[3]
    buttons = [(str(points), f"add_few_assists__{str(player_id)}__{game_id}__{played_at}__{str(points)}") for points in
               range(21)]
    markup = create_markup(buttons, 4)
    await callback.message.edit_text("Сколько раздал пасов?", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("add_few_assists__"))
async def few_assist_func(callback):
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    played_at = callback.data.split("__")[3]
    points = int(callback.data.split("__")[4])
    await add_assist(game_id, player_id, points)
    buttons = [("↩️ Назад в игру", f"games__{game_id}__{played_at}")]
    markup = create_markup(buttons)
    await callback.message.edit_text("Красиво раздаёт пасы!", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("remove_assist__"))
async def remove_assist_func(callback):
    game_id = int(callback.data.split("__")[1])
    played_at = callback.data.split("__")[2]
    players_in_game = await find_players_with_something(int(game_id), something="assists")
    buttons = [
        (player["name"], f"unassist__{str(player['id'])}__{game_id}__{played_at}") for player in players_in_game
    ]
    buttons.append(("↩️ Назад в игру", f"games__{game_id}__{played_at}"))
    markup = create_markup(buttons, columns=2)
    await callback.message.edit_text("Кого отменяем?", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("unassist__"))
async def remove_assist_func(callback):
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    played_at = callback.data.split("__")[3]
    await remove_assist(game_id, player_id)
    buttons = [("↩️ Назад в игру", f"games__{game_id}__{played_at}")]
    markup = create_markup(buttons)
    await callback.message.edit_text("Галя, отмена", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("add_autogoal__"))
async def add_autogoal_func(callback):
    game_id = int(callback.data.split("__")[1])
    played_at = callback.data.split("__")[2]
    players_in_game = await find_players_in_game(int(game_id))
    buttons = [
        (player["name"], f"autogoal__{str(player['id'])}__{game_id}__{played_at}") for player in players_in_game
    ]
    buttons.append(("↩️ Назад в игру", f"games__{game_id}__{played_at}"))
    markup = create_markup(buttons, columns=2)
    await callback.message.edit_text("Кто забил в свои ворота?", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("autogoal__"))
async def autogoal_func(callback):
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    played_at = callback.data.split("__")[3]
    await add_autogoal(game_id, player_id)
    buttons = [("↩️ Назад в игру", f"games__{game_id}__{played_at}")]
    markup = create_markup(buttons)
    await callback.message.edit_text("Подставил команду...", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("remove_autogoal__"))
async def remove_autogoal_func(callback):
    game_id = int(callback.data.split("__")[1])
    played_at = callback.data.split("__")[2]
    players_in_game = await find_players_with_something(int(game_id), something="autogoals")
    buttons = [
        (player["name"], f"unautogoal__{str(player['id'])}__{game_id}__{played_at}") for player in players_in_game
    ]
    buttons.append(("↩️ Назад в игру", f"games__{game_id}__{played_at}"))
    markup = create_markup(buttons, columns=2)
    await callback.message.edit_text("Кого отменяем?", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("unautogoal__"))
async def remove_autogoal_func(callback):
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    played_at = callback.data.split("__")[3]
    await remove_autogoal(game_id, player_id)
    buttons = [("↩️ Назад в игру", f"games__{game_id}__{played_at}")]
    markup = create_markup(buttons)
    await callback.message.edit_text("Галя, отмена", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("results__"))
async def results_func(callback):
    game_id = int(callback.data.split("__")[1])
    played_at = callback.data.split("__")[2]
    msg = await results_of_the_game(game_id)
    buttons = [("↩️ Назад в игру", f"games__{game_id}__{played_at}")]
    markup = create_markup(buttons)
    await callback.message.edit_text(msg, reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("game_delete__"))
async def delete_game_func(callback, state):
    game_id = int(callback.data.split("__")[1])
    played_at = callback.data.split("__")[2]
    buttons = [
        ("Да", f"yes_delete__{game_id}"),
        ("Нет", f"games__{game_id}__{played_at}")
    ]
    markup = create_markup(buttons)
    await callback.message.edit_text("Уверен? Вместе с игрой удалятся все результаты игроков", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("point_player__"))
async def point_player_func(callback):
    game_id = int(callback.data.split("__")[1])
    played_at = callback.data.split("__")[2]
    points = int(callback.data.split("__")[3])
    players_in_game = await find_players_in_game(int(game_id))
    buttons = [
        (player["name"], f"add_points__{str(player['id'])}__{game_id}__{played_at}__{points}") for player in players_in_game
    ]
    buttons.append(("↩️ Назад в игру", f"games__{game_id}__{played_at}"))
    markup = create_markup(buttons, columns=2)
    await callback.message.edit_text("Кто выиграл?", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("more_points_player__"))
async def more_points_player_func(callback):
    game_id = int(callback.data.split("__")[1])
    played_at = callback.data.split("__")[2]
    players_in_game = await find_players_in_game(int(game_id))
    buttons = [
        (player["name"], f"added_points__{str(player['id'])}__{game_id}__{played_at}") for player in players_in_game
    ]
    buttons.append(("↩️ Назад в игру", f"games__{game_id}__{played_at}"))
    markup = create_markup(buttons, columns=2)
    await callback.message.edit_text("Кто выиграл?", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("added_points__"))
async def added_points(callback):
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    played_at = callback.data.split("__")[3]

    buttons = [(str(points), f"overall_points__{str(player_id)}__{game_id}__{played_at}__{str(points)}") for points in range(21)]
    markup = create_markup(buttons, 4)
    await callback.message.edit_text(f"Сколько очков добавляем?", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("add_points__"))
async def add_point_player(callback):
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    played_at = callback.data.split("__")[3]
    points = int(callback.data.split("__")[4])
    await add_points(game_id, player_id, points)
    buttons = [("↩️ Назад в игру", f"games__{game_id}__{played_at}")]
    markup = create_markup(buttons)
    await callback.message.edit_text(f"Добавили {points} {'очка' if points==3 else 'очко'}", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("overall_points__"))
async def add_overall_points_player(callback):
    print('tut?')
    player_id = int(callback.data.split("__")[1])
    game_id = int(callback.data.split("__")[2])
    played_at = callback.data.split("__")[3]
    overall_points = int(callback.data.split("__")[4])
    await add_overall_pts(game_id, player_id, overall_points)
    buttons = [("↩️ Назад в игру", f"games__{game_id}__{played_at}")]
    markup = create_markup(buttons)
    await callback.message.edit_text(f"Добавили {overall_points} очков", reply_markup=markup)


@router_all_games.callback_query(F.data.startswith("yes_delete__"))
async def yes_delete_game_func(callback, state):
    game_id = int(callback.data.split("__")[1])
    await delete_game(game_id)
    buttons = [
        ("↩️ Назад в меню", "start"),
    ]
    markup = create_markup(buttons)
    await callback.message.edit_text("Игра удалена", reply_markup=markup)
