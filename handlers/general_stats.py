from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import CallbackQuery
from aiogram_calendar import DialogCalendar, DialogCalendarCallback
from aiogram.fsm.context import FSMContext
from datetime import datetime

from keyboards.reply.create_markup import create_markup
from states.overall import OverallState
from pg_maker import (
    get_all_player_totals_goals,
    get_all_player_totals_assists,
    get_all_player_totals_goals_and_assists,
    get_top_players_by_points
)

router_general_stats = Router()


# ====== Вспомогалки для длинных сообщений ======
MAX_TG = 3900  # небольшой запас до лимита 4096

def back_markup():
    return create_markup([("↩️ Назад в меню", "start")])

def build_stats_messages(results, header: str):
    """Собираем список текстовых чанков <= MAX_TG с HTML-разметкой."""
    entries = []
    for num, player in enumerate(results, 1):
        if player['games_played'] == 0:
            continue

        username = f"@{player['username']}" if player['username'] else "—"
        block = (
            f"<b>{num}. {player['name']}</b> — {username}\n"
            f"⚽ Голы: {player['total_goals']}\n"
            f"🤝 Ассисты: {player['total_assists']}\n"
            f"🏟 Сыграно матчей: {player['games_played']}\n"
            f"🏅 Набрано очков: {player['total_points']}\n"
            #f"🏆 Набрано pts: {player['overall_pts']}\n"
        )
        if player.get('total_autogoals', 0) > 0:
            block += f"🤡 Автоголы: {player['total_autogoals']}\n"
        block += "______________ \n\n"
        entries.append(block)

    chunks = []
    current = header
    sep = "—" * 22 + "\n"
    if entries:
        current += sep

    for block in entries:
        if len(current) + len(block) > MAX_TG:
            chunks.append(current.rstrip())
            current = block
        else:
            current += block

    if current.strip():
        chunks.append(current.rstrip())

    return chunks

async def send_chunks(message, chunks, edit: bool):
    """Отправляем/редактируем длинный текст по чанкам. Кнопки — только под последним блоком."""
    if not chunks:
        chunks = ["ℹ️ Данных нет"]

    if edit:
        # первый чанк — редактируем
        await message.edit_text(chunks[0], parse_mode="HTML")
        # промежуточные — отдельными сообщениями
        for mid in chunks[1:-1]:
            await message.answer(mid, parse_mode="HTML")
        # последний — с кнопкой «Назад»
        if len(chunks) > 1:
            await message.answer(chunks[-1], reply_markup=back_markup(), parse_mode="HTML")
        else:
            await message.edit_text(chunks[0], reply_markup=back_markup(), parse_mode="HTML")
    else:
        # обычная отправка
        await message.answer(chunks[0], parse_mode="HTML")
        for mid in chunks[1:-1]:
            await message.answer(mid, parse_mode="HTML")
        if len(chunks) > 1:
            await message.answer(chunks[-1], reply_markup=back_markup(), parse_mode="HTML")
        else:
            # единичный чанк — сразу с кнопкой
            await message.answer(chunks[0], reply_markup=back_markup(), parse_mode="HTML")


# ---------- МЕНЮ / ОБЩАЯ СТАТИСТИКА ----------
@router_general_stats.message(Command("general_stats"))
@router_general_stats.callback_query(F.data.startswith("general_stats_"))
async def general_stats_func(event, state: FSMContext):
    if isinstance(event, CallbackQuery):
        data = event.data
        message = event.message
        edit = True
    else:
        data = None
        message = event
        edit = False

    # Меню
    if data is None:
        kb = create_markup([
            ("⚽ Голы (всё время)", "general_stats_goal"),
            ("🤝 Ассисты (всё время)", "general_stats_assist"),
            ("⚽+🤝 Гол+пас (всё время)", "general_stats_goal_and_assist"),
            ("🏆 PTS (всё время)", "general_stats_overall_pts"),                # добавил
            ("📅 ⚽ Голы за период", "general_stats_goal_period"),
            ("📅 🤝 Ассисты за период", "general_stats_assist_period"),
            ("📅 ⚽+🤝 Гол+пас за период", "general_stats_goal_and_assist_period"),
            ("📅 🏆 PTS за период", "see_overall_pts_period"),                  # добавил
            ("📅 🏅 Очки за период", "general_stats_points_period"),
            ("↩️ Назад в меню", "start"),
        ], columns=2)
        await message.answer("Выбери раздел статистики:", reply_markup=kb)
        return

    # Ветки "за период" из general_stats_*
    if data.endswith("_period"):
        stats_type = data.removesuffix("_period")  # general_stats_goal / _assist / _goal_and_assist / _points / _overall_pts (если сделаешь единообразно)
        await state.set_state(OverallState.calendar)
        await state.update_data(stage="start", stats_type=stats_type)
        await message.answer(
            "Выбери дату начала отслеживания",
            reply_markup=await DialogCalendar().start_calendar(
                year=datetime.now().year, month=datetime.now().month
            ),
        )
        return

    # «всё время»
    if data == "general_stats_goal":
        results = await get_all_player_totals_goals()
        header = "<b>ТАБЛИЦА ЛУЧШИХ ПО ГОЛАМ</b>\n\n"
    elif data == "general_stats_assist":
        results = await get_all_player_totals_assists()
        header = "<b>ТАБЛИЦА ЛУЧШИХ ПО АССИСТАМ</b>\n\n"
    elif data == "general_stats_goal_and_assist":
        results = await get_all_player_totals_goals_and_assists()
        header = "<b>ТАБЛИЦА ЛУЧШИХ ПО ГОЛ+ПАС</b>\n\n"
    elif data == "general_stats_points":
        results = await get_top_players_by_points()
        header = "<b>ТАБЛИЦА ЛУЧШИХ ПО ОЧКАМ</b>\n\n"
    elif data == "general_stats_overall_pts":
        results = await get_top_players_by_points(overall_pts=True)
        header = "<b>ТАБЛИЦА ЛУЧШИХ ПО PTS</b>\n\n"
    else:
        kb = create_markup([("↩️ Назад в меню", "start")])
        await message.answer("Неизвестный тип статистики.", reply_markup=kb)
        return

    chunks = build_stats_messages(results, header)
    await send_chunks(message, chunks, edit)


@router_general_stats.callback_query(F.data.in_({
    "see_goals_period",
    "see_assists_period",
    "see_goals_and_assists_period",
    "see_points_period",
    "see_overall_pts_period",
}))
async def start_period_from_stats_menu(call: CallbackQuery, state: FSMContext):
    mapping = {
        "see_goals_period": "general_stats_goal",
        "see_assists_period": "general_stats_assist",
        "see_goals_and_assists_period": "general_stats_goal_and_assist",
        "see_points_period": "general_stats_points",
        "see_overall_pts_period": "general_stats_overall_pts",
    }
    stats_type = mapping[call.data]
    await state.set_state(OverallState.calendar)
    await state.update_data(stage="start", stats_type=stats_type)
    await call.message.answer(
        "Выбери дату начала отслеживания",
        reply_markup=await DialogCalendar().start_calendar(
            year=datetime.now().year, month=datetime.now().month
        ),
    )


async def end_period(call_or_cbq, state: FSMContext):
    await state.update_data(stage="end")
    target_msg = call_or_cbq.message if isinstance(call_or_cbq, CallbackQuery) else call_or_cbq
    await target_msg.answer(
        "Выбери дату конца отслеживания",
        reply_markup=await DialogCalendar().start_calendar(
            year=datetime.now().year, month=datetime.now().month
        ),
    )


@router_general_stats.callback_query(StateFilter(OverallState.calendar), DialogCalendarCallback.filter())
async def process_dialog_calendar(callback_query: CallbackQuery, callback_data, state: FSMContext):
    selected, date = await DialogCalendar().process_selection(callback_query, callback_data)
    if not selected:
        return

    data = await state.get_data()
    stage = data.get("stage")

    if stage == "start":
        await state.update_data(start=date.strftime("%Y-%m-%d"))
        await end_period(callback_query, state)
        return

    if stage == "end":
        await state.update_data(end=date.strftime("%Y-%m-%d"))
        data = await state.get_data()
        stats_type = data.get("stats_type")  # 'general_stats_goal' / '..._assist' / '..._goal_and_assist' / 'general_stats_points' / 'general_stats_overall_pts'

        start_date = datetime.strptime(data["start"], "%Y-%m-%d").date()
        end_date   = datetime.strptime(data["end"], "%Y-%m-%d").date()

        # Вызываем нужную функцию с периодом
        if stats_type == "general_stats_goal":
            results = await get_all_player_totals_goals(start_date, end_date)
            header = (f"<b>ТАБЛИЦА ЛУЧШИХ ПО ГОЛАМ</b>\n"
                      f"📅 с {start_date.strftime('%d %B')} по {end_date.strftime('%d %B')}\n\n")
        elif stats_type == "general_stats_assist":
            results = await get_all_player_totals_assists(start_date, end_date)
            header = (f"<b>ТАБЛИЦА ЛУЧШИХ ПО АССИСТАМ</b>\n"
                      f"📅 с {start_date.strftime('%d %B')} по {end_date.strftime('%d %B')}\n\n")
        elif stats_type == "general_stats_points":
            results = await get_top_players_by_points(start_date, end_date)
            header = (f"<b>ТАБЛИЦА ЛУЧШИХ ПО ОЧКАМ</b>\n"
                      f"📅 с {start_date.strftime('%d %B')} по {end_date.strftime('%d %B')}\n\n")
        elif stats_type == "general_stats_overall_pts":
            results = await get_top_players_by_points(start_date, end_date, overall_pts=True)
            header = (f"<b>ТАБЛИЦА ЛУЧШИХ ПО PTS</b>\n"
                      f"📅 с {start_date.strftime('%d %B')} по {end_date.strftime('%d %B')}\n\n")
        else:
            results = await get_all_player_totals_goals_and_assists(start_date, end_date)
            header = (f"<b>ТАБЛИЦА ЛУЧШИХ ПО ГОЛ+ПАС</b>\n"
                      f"📅 с {start_date.strftime('%d %B')} по {end_date.strftime('%d %B')}\n\n")

        chunks = build_stats_messages(results, header)
        await state.clear()
        # тут мы редактируем исходное сообщение календаря — значит edit=True
        await send_chunks(callback_query.message, chunks, edit=True)
