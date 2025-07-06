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

async def get_buttons():
    game = await get_latest_game()
    game_id = game['id']
    return [
        ("Иду",         f"yes__{game_id}"),
        ("Иду + 1",     f"yes_plus__{game_id}"),
        ("Не иду",      f"no__{game_id}"),
        ("Пока думаю",  f"maybe__{game_id}"),
    ]

async def get_msg() -> str:
    game = await get_latest_game()
    game_id = game['id']
    going_players = await find_players_in_game(game_id)
    all_players_from_db = await all_players()
    player_map = {p['username']: p['name'] for p in all_players_from_db}

    no_users = no_tracks.get(game_id, set())
    maybe_users = maybe_tracks.get(game_id, set())
    plus_users = pluses.get(game_id, set())

    going = [p for p in going_players if p['username'] not in maybe_users and p['username'] not in no_users]
    plus_count = len([u for u in plus_users if u in {p['username'] for p in going}])
    total_going = len(going) + plus_count
    game_date = game["played_at"]
    label = f"{game_date.day:02d} {MONTHS_GENITIVE[game_date.month]} {game_date.year}"

    msg = f"*Игра во вторник ({label}). Кто в деле?*\n"
    msg += f"Всего идут: *{total_going}*\n\n"

    # Идут
    msg += "*Идут:*\n"
    if going:
        for idx, p in enumerate(going, 1):
            plus = ' +1' if p['username'] in plus_users else ''
            msg += f"{idx}. {p['name']} @{p['username']}{plus}\n"
    else:
        msg += "\n"
    msg += "\n"
    # Не идут
    msg += "*Не идут:*\n"
    if no_users:
        for idx, u in enumerate(no_users, 1):
            full_name = player_map.get(u, u)
            msg += f"{idx}. {full_name} @{u if u else ''}\n"
    else:
        msg += "\n"
    msg += "\n"
    # Думают
    msg += "*Думают:*\n"
    if maybe_users:
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
            parse_mode="Markdown"
        )


@router_message.callback_query(F.data.startswith(("yes__", "no__", "yes_plus__", "maybe__")))
async def toggle_player_in_game(event: CallbackQuery):
    user = event.from_user
    player_username = user.username or ''
    print(player_username, "USERNAME")
    player_first_name = user.first_name

    action, game_id_str = event.data.split("__")
    game_id = int(game_id_str)

    player_id = await find_player_id(player_username)
    print(player_id, "ID")
    if not player_id:
        player_id = await add_player(player_first_name, player_username)

    pluses.get(game_id, set()).discard(player_username)
    no_tracks.get(game_id, set()).discard(player_username)
    maybe_tracks.get(game_id, set()).discard(player_username)

    if action == "yes" or action == "yes__":
        await register_player_in_game(game_id, player_id)
    elif action.startswith("yes_plus"):
        await register_player_in_game(game_id, player_id)
        pluses.setdefault(game_id, set()).add(player_username)
    elif action == "no" or action == "no__":
        await unregister_player_from_game(game_id, player_id)
        no_tracks.setdefault(game_id, set()).add(player_username)
    elif action == "maybe" or action == "maybe__":
        await unregister_player_from_game(game_id, player_id)
        maybe_tracks.setdefault(game_id, set()).add(player_username)


    buttons = await get_buttons()
    markup = create_markup(buttons, columns=2)
    msg = await get_msg()
    try:
        await event.message.edit_text(msg, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        print(f"Error editing message: {e}")
