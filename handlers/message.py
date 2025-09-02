from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from config_data import config
from loader import bot
from keyboards.reply.create_markup import create_markup
from utils.calend import MONTHS_GENITIVE
from pg_maker import (
    add_player,
    all_players,
    all_chats,
    get_latest_game,
    register_player_in_game,
    unregister_player_from_game,
    find_player_id,
    find_players_in_game
)

router_message = Router()

CHATS = config.CHATS


pluses = {}
no_tracks = {}
maybe_tracks = {}
going_order = {}

async def get_buttons():
    game = await get_latest_game()
    game_id = game['id']
    return [
        ("Иду",        f"yes__{game_id}"),
        ("Иду +1",     f"yes_plus1__{game_id}"),
        ("Иду +2",     f"yes_plus2__{game_id}"),
        ("Иду +3",     f"yes_plus3__{game_id}"),
        ("Не иду",     f"no__{game_id}"),
        ("Пока думаю", f"maybe__{game_id}"),
    ]

async def get_msg() -> str:
    game = await get_latest_game()
    game_id = game['id']
    going_players = await find_players_in_game(game_id)
    all_players_from_db = await all_players()
    player_map = {p['username']: p['name'] for p in all_players_from_db}

    no_users = no_tracks.get(game_id, set())
    maybe_users = maybe_tracks.get(game_id, set())
    plus_users = pluses.get(game_id, {})

    going = [p for p in going_players if p['username'] not in maybe_users and p['username'] not in no_users]

    # считаем общее число + учитываем плюсы
    total_going = len(going) + sum(plus_users.get(p['username'], 0) for p in going)
    game_date = game["played_at"]
    label = f"{game_date.day:02d} {MONTHS_GENITIVE[game_date.month]} {game_date.year}"

    msg = f"<b>Игра во вторник ({label}). Кто в деле?</b>\n\n"
    msg += f"Всего идут: <b>{total_going}</b>\n\n"

    # Идут
    if going:
        msg += "<b>Идут:</b>\n"
        for idx, p in enumerate(going, 1):
            extra = plus_users.get(p['username'], 0)
            plus_label = f" +{extra}" if extra > 0 else ""
            msg += f"{idx}. {p['name']} @{p['username']}{plus_label}\n"
    else:
        msg += "\n"

    # Не идут
    if no_users:
        msg += "<b>Не идут:</b>\n"
        for idx, u in enumerate(no_users, 1):
            full_name = player_map.get(u, u)
            msg += f"{idx}. {full_name} @{u if u else ''}\n"
    else:
        msg += "\n"
    msg += "\n"
    # Думают
    if maybe_users:
        msg += "<b>Думают:</b>\n"
        for idx, u in enumerate(maybe_users, 1):
            full_name = player_map.get(u, u)
            msg += f"{idx}. {full_name} @{u if u else ''}\n"
    else:
        msg += "\n"
    url = "https://maps.app.goo.gl/gthro3uEh1rHKPAu7?g\\_st=it"
    msg += f"\n\nИграем в 20:00 по адресу Soroksari utca 79-91 {url}\n"

    return msg


@router_message.message(Command("message"))
@router_message.callback_query(F.data == "message")
async def message_func(event):
    buttons = await get_buttons()
    markup = create_markup(buttons, columns=2)
    msg = await get_msg()

    chats_from_pg = await all_chats()

    for chat in chats_from_pg:
        await bot.send_message(
            chat_id=chat["chat_id"],
            text=msg,
            reply_markup=markup,
            parse_mode="HTML"
        )


@router_message.callback_query(F.data.startswith(("yes__", "no__", "yes_plus", "maybe__")))
async def toggle_player_in_game(event: CallbackQuery):
    user = event.from_user
    player_username = user.username or ''
    player_first_name = user.first_name

    action, game_id_str = event.data.split("__")
    game_id = int(game_id_str)

    player_id = await find_player_id(player_username)
    if not player_id:
        player_id = await add_player(player_first_name, player_username)

    # очистка старых статусов
    if game_id in pluses:
        pluses[game_id].pop(player_username, None)
    no_tracks.get(game_id, set()).discard(player_username)
    maybe_tracks.get(game_id, set()).discard(player_username)

    if action == "yes":
        await register_player_in_game(game_id, player_id)

    elif action.startswith("yes_plus"):
        await register_player_in_game(game_id, player_id)
        pluses.setdefault(game_id, {})
        if action == "yes_plus1":
            pluses[game_id][player_username] = 1
        elif action == "yes_plus2":
            pluses[game_id][player_username] = 2
        elif action == "yes_plus3":
            pluses[game_id][player_username] = 3

    elif action == "no":
        await unregister_player_from_game(game_id, player_id)
        no_tracks.setdefault(game_id, set()).add(player_username)

    elif action == "maybe":
        await unregister_player_from_game(game_id, player_id)
        maybe_tracks.setdefault(game_id, set()).add(player_username)

    buttons = await get_buttons()
    markup = create_markup(buttons, columns=2)
    msg = await get_msg()
    try:
        await event.message.edit_text(msg, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print(f"Error editing message: {e}")
