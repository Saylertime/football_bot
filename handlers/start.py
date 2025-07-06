from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery
from aiogram.enums.chat_type import ChatType

from pg_maker import create_schema
from keyboards.reply.create_markup import create_markup
from config_data import config

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

    buttons = [
        # ("👤 Добавить игрока в базу", "new_player"),
        # ("👉🏻🗑️ Удалить игрока", "delete_player"),
        ("👥Игроки", "players"),
        ("🎮 Новая игра", "add_game"),
        ("🍿 Все игры", "all_games"),
        ("📊 Моя статистика", "my_stats"),
        ("🌐 Общая стата за всё время", "general_stats"),
        ("💬 СООБЩЕНИЕ В ЧАТ", "message"),
    ]

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
