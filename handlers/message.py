from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from config_data import config
from loader import bot
from keyboards.reply.create_markup import create_markup
from utils.calend import MONTHS_GENITIVE

from pg_maker import (
    add_player,
    all_players,
    all_chats,
    get_latest_game,
    find_player_id,

    # ОСНОВА
    find_players_in_game,
    add_player_to_game_main,
    remove_player_from_game_main,

    # РЕЗЕРВ
    add_player_to_reserve,
    remove_player_from_reserve,
    find_reserve_players,
    pop_first_from_reserve,
)

router_message = Router()

TZ = ZoneInfo("Europe/Budapest")
CAPACITY = 18

# ПЛЮСЫ — только информация (НЕ влияют на места)
# {game_id: {username: 0/1/2/3}}
pluses: dict[int, dict[str, int]] = {}

no_tracks: dict[int, set[str]] = {}
maybe_tracks: dict[int, set[str]] = {}


def get_plus(game_id: int, username: str) -> int:
    return int(pluses.get(game_id, {}).get(username, 0) or 0)

def need_slots_for(game_id: int, username: str, plus_override: int | None = None) -> int:
    plus = get_plus(game_id, username) if plus_override is None else int(plus_override)
    return 1 + max(0, plus)

async def main_slots_used(game_id: int, exclude_username: str | None = None) -> int:
    main_list = await find_players_in_game(game_id)
    used = 0
    for p in main_list:
        uname = p.get("username") or ""
        if exclude_username and uname == exclude_username:
            continue
        used += need_slots_for(game_id, uname)
    return used

def plus_label(game_id: int, username: str) -> str:
    cnt = get_plus(game_id, username)
    return f" +{cnt}" if cnt > 0 else ""


def now_local() -> datetime:
    return datetime.now(TZ)


def is_plus_enabled(game, hours_before: int = 32) -> bool:
    """
    Плюсы доступны за N часов до игры.
    Если played_at — date, считаем время игры 20:00.
    """
    played_at = game["played_at"]

    if isinstance(played_at, datetime):
        dt = played_at
    else:
        dt = datetime.combine(played_at, time(20, 0))

    # приводим к TZ
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(TZ)
    else:
        dt = dt.astimezone(TZ)

    open_at = dt - timedelta(hours=hours_before)
    return now_local() >= open_at


async def auto_promote_from_reserve(game_id: int) -> list[dict]:
    """
    Автоподнятие из резерва в основу.
    Возвращает список поднятых игроков:
    [{id, name, username}, ...]
    """
    promoted_players = []

    while True:
        used = await main_slots_used(game_id)
        free = CAPACITY - used
        if free <= 0:
            break

        reserve = await find_reserve_players(game_id)
        if not reserve:
            break

        candidate = None
        for p in reserve:
            uname = p.get("username") or ""
            need = need_slots_for(game_id, uname)
            if need <= free:
                candidate = p
                break

        if not candidate:
            break

        player_id = candidate["id"]
        await remove_player_from_reserve(game_id, player_id)
        await add_player_to_game_main(game_id, player_id)

        promoted_players.append(candidate)

    return promoted_players


async def notify_promoted(players: list[dict]):
    if not players:
        return

    chats = await all_chats()
    for p in players:
        if not p.get("username"):
            continue

        text = f"🎉 @{p['username']}, ты в игре!"

        for chat in chats:
            await bot.send_message(
                chat_id=chat["chat_id"],
                text=text
            )


async def get_buttons(game_id: int):
    game = await get_latest_game()
    plus_ok = is_plus_enabled(game) if game else False

    buttons = [("Иду", f"yes__{game_id}")]

    # Плюсы как информация (доступны по времени, как у тебя было)
    if plus_ok:
        buttons += [
            ("Иду +1", f"yes_plus1__{game_id}"),
            ("Иду +2", f"yes_plus2__{game_id}"),
            ("Иду +3", f"yes_plus3__{game_id}"),
        ]

    buttons += [
        ("Не иду", f"no__{game_id}"),
        ("Пока думаю", f"maybe__{game_id}"),
    ]
    return buttons


async def build_message(game_id: int) -> str:
    game = await get_latest_game()
    if not game:
        return "❗️Нет ни одной созданной игры."

    # основа и резерв из БД
    main_list = await find_players_in_game(game_id)
    reserve_list = await find_reserve_players(game_id)

    main_list.sort(key=lambda p: p.get("joined_at"))
    reserve_list.sort(key=lambda p: p.get("added_at"))

    all_players_from_db = await all_players()
    player_map = {p["username"]: p["name"] for p in all_players_from_db}

    def get_plus_cnt(game_id: int, username: str) -> int:
        return int(pluses.get(game_id, {}).get(username, 0) or 0)

    occupied_slots = 0
    for p in main_list:
        uname = p.get("username") or ""
        occupied_slots += 1 + get_plus_cnt(game_id, uname)

    remaining = max(0, CAPACITY - occupied_slots)

    game_date = game["played_at"]
    label = f"{game_date.day:02d} {MONTHS_GENITIVE[game_date.month]} {game_date.year}"

    msg = f"<b>Игра во вторник ({label}). Кто в деле?</b>\n\n"
    msg += f"В основе: <b>{occupied_slots}</b>\n"
    msg += f"Свободных мест: <b>{remaining}</b>\n"

    if not is_plus_enabled(game):
        msg += "\n⚠️ Возможность добавлять плюсы откроется в понедельник в 12 часов\n"

    msg += "\n"

    # ОСНОВА
    if main_list:
        msg += "<b>Идут:</b>\n"
        for idx, p in enumerate(main_list, 1):
            uname = p.get("username") or ""
            at = f" @{uname}" if uname else ""
            msg += f"{idx}. {p['name']}{at}{plus_label(game_id, uname)}\n"
        msg += "\n"


    # РЕЗЕРВ (тоже показываем плюсики, если человек их выставлял)
    if reserve_list:
        msg += "<b>Резерв:</b>\n"
        for idx, p in enumerate(reserve_list, 1):
            uname = p.get("username") or ""
            at = f" @{uname}" if uname else ""
            msg += f"{idx}. {p['name']}{at}{plus_label(game_id, uname)}\n"
        msg += "\n"

    # НЕ ИДУТ (память)
    no_users = no_tracks.get(game_id, set())
    if no_users:
        msg += "<b>Не идут:</b>\n"
        for idx, u in enumerate(no_users, 1):
            full_name = player_map.get(u, u)
            at = f" @{u}" if u else ""
            msg += f"{idx}. {full_name}{at}\n"
        msg += "\n"

    # ДУМАЮТ (память)
    maybe_users = maybe_tracks.get(game_id, set())
    if maybe_users:
        msg += "<b>Думают:</b>\n"
        for idx, u in enumerate(maybe_users, 1):
            full_name = player_map.get(u, u)
            at = f" @{u}" if u else ""
            msg += f"{idx}. {full_name}{at}\n"
        msg += "\n"

    url = "https://maps.app.goo.gl/gthro3uEh1rHKPAu7?g\\_st=it"
    msg += f"Играем в 20:00 по адресу Soroksari utca 79-91 {url}\n"
    return msg


@router_message.message(Command("message"))
@router_message.callback_query(F.data == "message")
async def message_func(event):
    game = await get_latest_game()
    if not game:
        if hasattr(event, "message") and event.message:
            await event.message.answer("❗️Нет ни одной созданной игры.")
        else:
            await event.answer("❗️Нет ни одной созданной игры.", show_alert=True)
        return

    game_id = game["id"]
    buttons = await get_buttons(game_id)
    markup = create_markup(buttons, columns=2)
    msg = await build_message(game_id)

    chats_from_pg = await all_chats()
    for chat in chats_from_pg:
        await bot.send_message(
            chat_id=chat["chat_id"],
            text=msg,
            reply_markup=markup,
            parse_mode="HTML",
        )


@router_message.callback_query(F.data.startswith(("yes__", "yes_plus", "no__", "maybe__")))
async def toggle_player(event: CallbackQuery):
    game = await get_latest_game()
    if not game:
        await event.answer("❗️Нет ни одной созданной игры.", show_alert=True)
        return

    user = event.from_user
    username = user.username or ""
    name = user.first_name or "Без имени"

    action, game_id_str = event.data.split("__")
    game_id = int(game_id_str)

    player_id = await find_player_id(username)
    if not player_id:
        player_id = await add_player(name, username)

    no_tracks.get(game_id, set()).discard(username)
    maybe_tracks.get(game_id, set()).discard(username)

    # --- распарсим плюс ---
    new_plus = 0
    if action.startswith("yes_plus"):
        if action == "yes_plus1":
            new_plus = 1
        elif action == "yes_plus2":
            new_plus = 2
        elif action == "yes_plus3":
            new_plus = 3
        action = "yes"

    # --- YES (с плюсом или без) ---
    if action == "yes":
        main_list = await find_players_in_game(game_id)

        def plus_cnt(u: str) -> int:
            return int(pluses.get(game_id, {}).get(u, 0) or 0)

        # кто уже в основе?
        in_main = any(p.get("username") == username for p in main_list)

        # занятые слоты сейчас
        occupied = 0
        for p in main_list:
            u = p.get("username") or ""
            occupied += 1 + plus_cnt(u)

        remaining = CAPACITY - occupied  # может быть <= 0

        old_plus = plus_cnt(username)
        old_need = 1 + old_plus
        new_need = 1 + new_plus  # важно: учитываем самого игрока!

        if in_main:
            # если игрок уже в основе, нельзя "выкидывать" его в резерв при нажатии "Иду"
            # Проверяем место на изменение плюса: освобождаем его старые слоты и проверяем новые
            available_if_recalc = remaining + old_need
            if new_need > available_if_recalc:
                await event.answer(
                    f"⚠️ Не хватает мест для +{new_plus}. Свободно: {available_if_recalc - 1} (без учёта тебя).",
                    show_alert=True
                )
                # ничего не меняем
            else:
                pluses.setdefault(game_id, {})
                pluses[game_id][username] = new_plus
                await event.answer("✅", show_alert=False)

        else:
            # игрок не в основе: пытаемся добавить
            if new_need > remaining:
                # мест не хватает — в резерв
                try:
                    await add_player_to_reserve(game_id, player_id, added_by=user.id)
                    await remove_player_from_game_main(game_id, player_id)
                    await event.answer("⏳ Мест не хватает — добавил тебя в резерв. \n\n You are in RESERVE", show_alert=True)
                    # плюс можно сохранить (чтобы отображался в резерве), либо сбросить — на твой вкус
                    pluses.setdefault(game_id, {})
                    pluses[game_id][username] = new_plus
                except Exception as e:
                    print("RESERVE ERROR:", repr(e))
                    await bot.send_message(chat_id=68086662, text=str(e))
                    return

            else:
                # влезает — в основу
                await remove_player_from_reserve(game_id, player_id)
                await add_player_to_game_main(game_id, player_id)
                pluses.setdefault(game_id, {})
                pluses[game_id][username] = new_plus
                await event.answer("✅ Ты в основе!", show_alert=False)

    elif action == "no":
        await remove_player_from_game_main(game_id, player_id)
        await remove_player_from_reserve(game_id, player_id)
        no_tracks.setdefault(game_id, set()).add(username)
        pluses.get(game_id, {}).pop(username, None)
        promoted = await auto_promote_from_reserve(game_id)
        await notify_promoted(promoted)

    elif action == "maybe":
        await remove_player_from_game_main(game_id, player_id)
        await remove_player_from_reserve(game_id, player_id)
        maybe_tracks.setdefault(game_id, set()).add(username)
        pluses.get(game_id, {}).pop(username, None)
        promoted = await auto_promote_from_reserve(game_id)
        await notify_promoted(promoted)

    # обновляем сообщение
    buttons = await get_buttons(game_id)
    markup = create_markup(buttons, columns=2)
    msg = await build_message(game_id)
    try:
        await event.message.edit_text(msg, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        print(f"Error editing message: {e}")
