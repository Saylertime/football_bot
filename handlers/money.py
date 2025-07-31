from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from config_data import config
from loader import bot
from keyboards.reply.create_markup import create_markup
from utils.calend import MONTHS_GENITIVE
from states.overall import OverallState
from pg_maker import (
    add_player,
    all_players,
    all_chats,
    get_latest_game,
    register_player_in_game,
    unregister_player_from_game,
    find_player_id,
    find_players_in_game,
    mark_player_paid,
    get_paid_players,
    remove_payment,
    add_summa,
    find_summa
)

router_money = Router()
CHATS = config.CHATS
maybe_tracks = {}

async def get_buttons():
    game = await get_latest_game()
    game_id = game['id']
    return [
        ("Сдал", f"money__{game_id}"),
        ("Не сдал", f"no_money__{game_id}"),
    ]

async def get_msg_money():
    game = await get_latest_game()
    game_id = game['id']
    going_players = await find_players_in_game(game_id)  # все записавшиеся
    all_players_from_db = await all_players()
    summa = await find_summa(game_id)

    player_map = {p['username']: p['name'] for p in all_players_from_db}
    maybe_users = set(await get_paid_players(game_id))

    # Исключаем сдавших из списка "не сдали"
    unpaid_players = [p for p in going_players if p["username"] not in maybe_users]


    msg = f"Скидываемся по <b>{summa}</b> HUF с человека\n\n"

    if maybe_users:
        msg += "\n<b>Уже сдали:</b>\n"
        for idx, u in enumerate(maybe_users, 1):
            full_name = player_map.get(u, u)
            msg += f"{idx}. {full_name} @{u}\n"

    msg += "\n"

    if unpaid_players:
        msg += "<b>Не сдали:</b>\n"
        for idx, p in enumerate(unpaid_players, 1):
            msg += f"{idx}. {p['name']} @{p['username']}\n"
    else:
        msg += "\n"
    return msg


@router_money.message(Command("money"))
@router_money.callback_query(F.data == "money")
async def money_func(event, state):
    await event.message.answer("Сколько с человека?")
    await state.set_state(OverallState.money)


@router_money.message(OverallState.money)
async def changed_name_func(message, state):
    game = await get_latest_game()
    game_id = game['id']
    money_sum = int(message.text.strip())
    await add_summa(game_id, money_sum)
    print(money_sum)
    buttons = await get_buttons()
    markup = create_markup(buttons, columns=2)
    msg = await get_msg_money()

    chats_from_pg = await all_chats()

    for chat in chats_from_pg:
        await bot.send_message(
            chat_id=chat["chat_id"],
            text=msg,
            reply_markup=markup,
            parse_mode="HTML"
        )


@router_money.callback_query(F.data.startswith(("money__", "no_money__")))
async def toggle_player_in_game(event: CallbackQuery):
    user = event.from_user
    username = user.username or ''
    action, game_id_str = event.data.split("__")
    game_id = int(game_id_str)

    # Проверяем, записан ли пользователь на игру
    going_players = await find_players_in_game(game_id)
    going_usernames = {p["username"] for p in going_players}

    if username not in going_usernames:
        await event.answer("Ты не играл, зачем кнопки жмешь))", show_alert=True)
        return

    player_id = await find_player_id(username)
    if player_id:
        if action == "money" or action == "money__":
            await mark_player_paid(game_id, player_id)
        elif action == "no_money" or action == "no_money__":
            await remove_payment(game_id, player_id)

    buttons = await get_buttons()
    markup = create_markup(buttons, columns=2)
    msg = await get_msg_money()
    try:
        await event.message.edit_text(msg, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print(f"Error editing message: {e}")
