from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery
from aiogram.enums.chat_type import ChatType

from config_data import config
from pg_maker import create_schema, get_latest_game
from utils.calend import MONTHS_GENITIVE
from keyboards.reply.create_markup import create_markup


router_start = Router()
admins = config.ADMINS


@router_start.message(CommandStart())
@router_start.callback_query(F.data == "start")
async def command_start_handler(message):
    if isinstance(message, CallbackQuery):
        message = message.message
    await create_schema()

    if message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        await add_chat(message.chat.title or "", str(message.chat.id))
    print(message.chat.id)
    print(message.chat.title)

    current_game = None

    try:
        current_game = await get_latest_game()
        game_id = str(current_game["id"])
        played_at = current_game.get("played_at")
        label = f"{played_at.day:02d} {MONTHS_GENITIVE[played_at.month]} {played_at.year}"
    except:
        print("Нет текущей игры")

    buttons = [
        ("🍿 Игры", "games"),
        ("👥 Игроки", "players"),
        ("📊 Статистика", "stats"),
        # ("📊 Моя статистика", "my_stats"),
        # ("🌐 Общая стата за всё время", "general_stats"),
        ("💬 СООБЩЕНИЕ В ЧАТ", "message"),
    ]

    if current_game:
        current_game_button = ("⚽💥 Текущая игра", f"games__{game_id}__{label}")
        buttons.insert(0, current_game_button)

    # buttons_for_admins = [
    #     ("💬 СООБЩЕНИЕ В ЧАТ", "message"),
    # ]
    #
    # if str(message.from_user.id) in admins:
    #     for button in buttons_for_admins:
    #         buttons.append(button)

    markup = create_markup(buttons)

    msg = "⬇⬇⬇ БОТ ДЛЯ БУДАПЕШСТКИХ ФУТБИКОВ ⬇⬇⬇"
    try:
        await message.edit_text(msg, reply_markup=markup)
    except:
        await message.answer(msg, reply_markup=markup)
