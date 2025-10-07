from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery
from aiogram.enums.chat_type import ChatType

from config_data import config
from pg_maker import create_schema, get_latest_game
from utils.calend import MONTHS_GENITIVE
from keyboards.reply.create_markup import create_markup


router_start = Router()

admins = ["68086662", "202583595", "469295831"]


@router_start.message(CommandStart())
@router_start.callback_query(F.data == "start")
async def command_start_handler(event):
    if isinstance(event, CallbackQuery):
        message = event.message
        user_id = str(event.from_user.id)
    else:
        message = event
        user_id = str(message.from_user.id)

    await create_schema()

    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        await add_chat(message.chat.title or "", str(message.chat.id))

    try:
        current_game = await get_latest_game()
        game_id = str(current_game["id"])
        played_at = current_game.get("played_at")
        label = f"{played_at.day:02d} {MONTHS_GENITIVE[played_at.month]} {played_at.year}"
    except Exception:
        current_game = None
        print("Нет текущей игры")


    buttons = []

    buttons_for_admins = [
        ("🍿 Игры", "games"),
        ("👥 Игроки", "players"),
        ("📊 Статистика", "stats"),
        ("💬 СООБЩЕНИЕ В ЧАТ", "message"),
        ("💰 ДЕНЬГИ", "money"),
    ]

    if current_game:
        current_game_button = ("⚽💥 Текущая игра", f"games__{game_id}__{label}")
        buttons_for_admins.insert(0, current_game_button)

    if user_id in admins:
        buttons.extend(buttons_for_admins)

    markup = create_markup(buttons)
    msg = "⬇⬇⬇ БОТ ДЛЯ БУДАПЕШТСКИХ ФУТБИКОВ ⬇⬇⬇"

    try:
        await message.edit_text(msg, reply_markup=markup)
    except:
        await message.answer(msg, reply_markup=markup)
