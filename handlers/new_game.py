from aiogram import Router, F
from aiogram_calendar import DialogCalendar, DialogCalendarCallback
from aiogram.filters import Command, StateFilter
from aiogram.types import CallbackQuery

from datetime import datetime, timedelta
from handlers.start import command_start_handler
from states.overall import OverallState
from pg_maker import add_game


router_add_game = Router()


@router_add_game.message(Command("add_game"))
@router_add_game.callback_query(F.data == "add_game")
async def add_game_func(message, state):
    if isinstance(message, CallbackQuery):
        message = message.message

    await state.set_state(OverallState.add_game)
    await message.answer(
        "Выбери дату",
        reply_markup=await DialogCalendar().start_calendar(
            year=datetime.now().year, month=datetime.now().month
        ),
    )


@router_add_game.callback_query(StateFilter(OverallState.add_game), DialogCalendarCallback.filter())
async def process_dialog_calendar(callback_query, callback_data, state):
    selected, date = await DialogCalendar().process_selection(
        callback_query, callback_data
    )

    if not selected:
        return

    await add_game(played_at=date)
    await state.clear()
    await callback_query.message.answer(f"Игра добавлена на {date:%d.%m.%Y} ✅")
    await command_start_handler(callback_query.message)
