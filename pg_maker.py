from contextlib import asynccontextmanager
from config_data import config
import asyncpg

dbname = config.DB_NAME
user = config.DB_USER
password = config.DB_PASSWORD
host = config.DB_HOST


@asynccontextmanager
async def db_connection():
    """Контекстный менеджер для асинхронного подключения к базе данных."""
    conn = await asyncpg.connect(
        database=dbname, user=user, password=password, host=host
    )
    try:
        yield conn
    finally:
        await conn.close()


async def create_schema():
    async with db_connection() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                title VARCHAR,
                chat_id VARCHAR UNIQUE NOT NULL
            );
        
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                username VARCHAR UNIQUE,  
                is_active BOOLEAN NOT NULL DEFAULT TRUE
            );
             
            CREATE TABLE IF NOT EXISTS games (
                id SERIAL PRIMARY KEY,
                played_at DATE NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS game_player_stats (
                game_id   INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE RESTRICT,
                goals     INTEGER NOT NULL DEFAULT 0,
                assists   INTEGER NOT NULL DEFAULT 0,
                autogoals   INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (game_id, player_id)
            );
            
            CREATE TABLE IF NOT EXISTS game_payments (
                game_id   INTEGER NOT NULL REFERENCES games(id) ON DELETE CASCADE,
                player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE RESTRICT,
                PRIMARY KEY (game_id, player_id)
            );
            
            CREATE TABLE IF NOT EXISTS game_sums (
                game_id INTEGER PRIMARY KEY REFERENCES games(id) ON DELETE CASCADE,
                summa INTEGER NOT NULL
            );
        """)


async def add_chat(title, chat_id):
    async with db_connection() as conn:
        sql = """
        INSERT INTO chats (title, chat_id)
        VALUES ($1, $2)
        """
        await conn.execute(sql, title, chat_id)


async def add_game(played_at):
    async with db_connection() as conn:
        sql = """
        INSERT INTO games (played_at)
        VALUES ($1)
        """
        await conn.execute(sql, played_at)


async def add_player(name, username=""):
    async with db_connection() as conn:
        new_id = await conn.fetchval(
            """
            INSERT INTO players (name, username)
            VALUES ($1, $2)
            RETURNING id;
            """,
            name, username
        )
    return new_id


async def delete_player(name):
    async with db_connection() as conn:
        sql = """
        DELETE FROM players
        WHERE name = $1 
        """
        print(name)
        await conn.execute(sql, name)


async def delete_game(game_id):
    async with db_connection() as conn:
        sql = """
        DELETE FROM games
        WHERE id = $1 
        """
        await conn.execute(sql, game_id)


async def find_player_name(username):
    async with db_connection() as conn:
        sql = """
        SELECT name
        FROM players
        WHERE username = $1
        """
        player = await conn.fetchrow(sql, username)
        return player


async def find_player_id(username):
    async with db_connection() as conn:
        sql = """
        SELECT id
        FROM players
        WHERE username = $1
        """
        player_id = await conn.fetchrow(sql, username)
        return player_id["id"] if player_id else None


async def all_players():
    async with db_connection() as conn:
        sql = """ 
        SELECT * from players
        """
        players = await conn.fetch(sql)
        return players


async def all_games():
    async with db_connection() as conn:
        sql = """ 
        SELECT * from games
        """
        players = await conn.fetch(sql)
        return players


async def all_my_games(player_id):
    async with db_connection() as conn:
        sql = """ 
        SELECT * from games g
        JOIN game_player_stats s ON g.id = s.game_id
        WHERE player_id = $1
        """
        players = await conn.fetch(sql, player_id)
        return players


async def my_stats_in_match(player_id, game_id):
    async with db_connection() as conn:
        sql = """ 
        SELECT goals, assists, autogoals from game_player_stats s
        JOIN games g ON g.id = s.game_id
        WHERE player_id = $1 AND game_id = $2 
        """
        stats = await conn.fetchrow(sql, player_id, game_id)
        return stats


async def register_player_in_game(game_id: int, player_id: int):
    async with db_connection() as conn:
        # сколько мест уже занято в основном составе
        sql_main = """
            SELECT COUNT(*) AS total
            FROM game_player_stats s
            WHERE s.game_id = $1 AND s.is_reserve = FALSE
        """
        total = await conn.fetchval(sql_main, game_id)

        CAPACITY = 18
        is_reserve = total >= CAPACITY

        # сохраняем запись
        sql_insert = """
            INSERT INTO game_player_stats (game_id, player_id, is_reserve, joined_at)
            VALUES ($1, $2, $3, NOW())
            ON CONFLICT (game_id, player_id)
            DO UPDATE SET is_reserve = EXCLUDED.is_reserve
        """
        await conn.execute(sql_insert, game_id, player_id, is_reserve)


async def unregister_player_from_game(game_id, player_id):
    print(game_id)
    print(player_id)
    async with db_connection() as conn:
        result = await conn.execute(
            """
            DELETE FROM game_player_stats
            WHERE game_id = $1 
              AND player_id = $2;
            """,
            game_id, player_id
        )
        print("DELETE result:", result)


async def add_goal(game_id, player_id, count=1):
    async with db_connection() as conn:
        sql = """
        INSERT INTO game_player_stats (game_id, player_id, goals, assists)
        VALUES ($1, $2, $3, 0)
        ON CONFLICT (game_id, player_id) DO UPDATE
          SET goals = game_player_stats.goals + $3;
        """
        await conn.execute(sql, game_id, player_id, count)


async def remove_goal(game_id, player_id):
    async with db_connection() as conn:
        sql = """
        UPDATE game_player_stats
        SET goals = 0
        WHERE game_id = $1 AND player_id = $2;
        """
        await conn.execute(sql, game_id, player_id)



async def add_assist(game_id, player_id, count=1):
    async with db_connection() as conn:
        sql = """
        INSERT INTO game_player_stats (game_id, player_id, goals, assists)
        VALUES ($1, $2, 0, $3)
        ON CONFLICT (game_id, player_id) DO UPDATE
          SET assists = game_player_stats.assists + $3;
        """
        await conn.execute(sql, game_id, player_id, count)


async def remove_assist(game_id, player_id):
    async with db_connection() as conn:
        sql = """
        UPDATE game_player_stats
        SET assists = 0
        WHERE game_id = $1 AND player_id = $2;
        """
        await conn.execute(sql, game_id, player_id)


async def add_autogoal(game_id, player_id, count=1):
    async with db_connection() as conn:
        sql = """
        INSERT INTO game_player_stats
          (game_id, player_id, goals, assists, autogoals)
        VALUES
          ($1, $2, 0, 0, $3)
        ON CONFLICT (game_id, player_id) DO UPDATE
          SET autogoals = game_player_stats.autogoals + $3;
        """
        await conn.execute(sql, game_id, player_id, count)


async def remove_autogoal(game_id, player_id, count=1):
    async with db_connection() as conn:
        sql = """
        INSERT INTO game_player_stats
          (game_id, player_id, goals, assists, autogoals)
        VALUES
          ($1, $2, 0, 0, 0)
        ON CONFLICT (game_id, player_id) DO UPDATE
          SET autogoals = GREATEST(game_player_stats.autogoals - $3, 0);
        """
        await conn.execute(sql, game_id, player_id, count)


async def add_points(game_id: int, player_id: int, points: int):
    async with db_connection() as conn:
        sql = """
        INSERT INTO game_player_stats (game_id, player_id, points)
        VALUES ($1, $2, $3)
        ON CONFLICT (game_id, player_id)
        DO UPDATE SET points = game_player_stats.points + EXCLUDED.points
        RETURNING points;
        """
        row = await conn.fetchrow(sql, game_id, player_id, points)
        return row["points"]


async def add_overall_pts(game_id: int, player_id: int, overall_pts: int):
    async with db_connection() as conn:
        sql = """
        INSERT INTO game_player_stats (game_id, player_id, overall_pts)
        VALUES ($1, $2, $3)
        ON CONFLICT (game_id, player_id)
        DO UPDATE SET overall_pts = game_player_stats.overall_pts + EXCLUDED.overall_pts
        RETURNING overall_pts;
        """
        row = await conn.fetchrow(sql, game_id, player_id, overall_pts)
        return row["overall_pts"]


async def find_players_without_game(game_id):
    async with db_connection() as conn:
        sql = """
        SELECT
          p.id,
          p.name,
          p.username
        FROM players p
        LEFT JOIN game_player_stats s
          ON s.player_id = p.id
          AND s.game_id   = $1 
        WHERE s.player_id IS NULL 
        OR s.is_reserve = TRUE;
    """
        rows = await conn.fetch(sql, game_id)
        return [dict(row) for row in rows]


async def find_players_in_game(game_id, is_reserve=None):
    async with db_connection() as conn:
        sql = """
        SELECT
          p.id,
          p.name,
          p.username,
          s.joined_at,
          s.is_reserve
        FROM players p
        JOIN game_player_stats s ON s.player_id = p.id
        WHERE s.game_id = $1
        """
        params = [game_id]

        # если передан фильтр
        if is_reserve is True:
            sql += " AND s.is_reserve = TRUE"
        elif is_reserve is False:
            sql += " AND s.is_reserve = FALSE"

        sql += " ORDER BY s.joined_at ASC, p.id ASC"

        rows = await conn.fetch(sql, *params)
        return [dict(row) for row in rows]


async def find_players_with_something(game_id, something):
    async with db_connection() as conn:
        sql = f"""
        SELECT
          p.id,
          p.name,
          p.username
        FROM players p
        LEFT JOIN game_player_stats s
          ON s.player_id = p.id
        WHERE s.game_id = $1 AND s.{something} >= 1;
        """
        rows = await conn.fetch(sql, game_id)
        return [dict(row) for row in rows]


async def results_of_the_game(game_id):
    async with db_connection() as conn:
        rows = await conn.fetch(
            """
            SELECT
              p.name,
              p.username,
              s.goals,
              s.assists,
              s.autogoals,
              s.points,
              s.overall_pts
            FROM game_player_stats s
            JOIN players p ON p.id = s.player_id
            WHERE s.game_id = $1 AND s.is_reserve is false
            ORDER BY s.goals DESC, s.assists DESC;
            """,
            game_id
        )

    if not rows:
        return "ℹ️ Для этой игры ещё нет статистики"

    def fmt_user(r):
        uname = f"@{r['username']}" if r["username"] else "—"
        return f"{r['name']} ({uname})"

    def ru_points(n: int) -> str:
        n = abs(int(n))
        if 11 <= n % 100 <= 14:
            return "очков"
        tail = n % 10
        if tail == 1:
            return "очко"
        if 2 <= tail <= 4:
            return "очка"
        return "очков"

    # топ-3 уникальных значения points (по убыванию)
    unique_points = sorted({int(r["points"]) for r in rows}, reverse=True)
    top3 = unique_points[:3]

    groups = []
    titles = ["🏆 Победители", "🥈 Второе место", "🥉 Третье место"]
    for idx, pts in enumerate(top3):
        members = [r for r in rows if int(r["points"]) == pts]
        if not members:
            continue
        title = f"{titles[idx]} (+{pts} {ru_points(pts)}):"
        groups.append((title, members))

    msg_parts = ["Результаты сегодняшних игр:\n"]

    for title, members in groups:
        msg_parts.append(title)
        for r in members:
            msg_parts.append(f"• {fmt_user(r)}")
        msg_parts.append("")

    msg_parts.append("—" * 22)

    # Индивидуальная статистика
    num = 1
    for r in rows:
        goals = r["goals"]
        assists = r["assists"]
        autogoals = r["autogoals"]
        if not (goals or assists or autogoals):
            continue

        name = r["name"]
        username = f"@{r['username']}" if r["username"] else ""
        overall = int(r["overall_pts"] or 0)

        msg_parts.append(f"{num}. {name} — {username}:")
        if goals:
            msg_parts.append(f"   ⚽ Голы: {goals}")
        if assists:
            msg_parts.append(f"   🤝 Ассисты: {assists}")
        if autogoals:
            msg_parts.append(f"   🤡 Автоголы: {autogoals}")
        # msg_parts.append(f"   🧮 Общие очки: {overall} {ru_points(overall)}")
        msg_parts.append("")
        num += 1

    return "\n".join(msg_parts)


async def get_latest_game():
    async with db_connection() as conn:
        sql = """
        SELECT id, played_at
        FROM games
        ORDER BY played_at DESC, id DESC
        LIMIT 1;
        """
        row = await conn.fetchrow(sql)
    return dict(row) if row else None


async def my_general_stats(player_id):
    async with db_connection() as conn:
        sql = """
        SELECT
          COUNT(*) AS matches_played,
          COALESCE(SUM(goals), 0) AS total_goals,
          COALESCE(SUM(assists), 0) AS total_assists,
          COALESCE(SUM(autogoals), 0) AS total_autogoals
        FROM game_player_stats
        WHERE player_id = $1
        """
        row = await conn.fetchrow(sql, player_id)
        return row


async def get_all_player_totals_goals_and_assists(start_date=None, end_date=None):
    sql = """
        SELECT
          p.id,
          p.name,
          p.username,

          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                   OR g.played_at BETWEEN $1 AND $2
              THEN s.goals ELSE 0 END), 0) AS total_goals,

          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                   OR g.played_at BETWEEN $1 AND $2
              THEN s.assists ELSE 0 END), 0) AS total_assists,

          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                   OR g.played_at BETWEEN $1 AND $2
              THEN s.autogoals ELSE 0 END), 0) AS total_autogoals,

          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                   OR g.played_at BETWEEN $1 AND $2
              THEN s.points ELSE 0 END), 0) AS total_points,

          COALESCE(COUNT(DISTINCT CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                   OR g.played_at BETWEEN $1 AND $2
              THEN g.id END), 0) AS games_played,

          -- Гол + ассист для сортировки
          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                   OR g.played_at BETWEEN $1 AND $2
              THEN s.goals + s.assists ELSE 0 END), 0) AS total_ga

        FROM players p
        LEFT JOIN game_player_stats s ON s.player_id = p.id
        LEFT JOIN games g ON g.id = s.game_id
        GROUP BY p.id, p.name, p.username
        ORDER BY total_ga DESC, total_goals DESC, total_points DESC;
    """
    async with db_connection() as conn:
        return await conn.fetch(sql, start_date, end_date)


async def get_all_player_totals_goals(start_date=None, end_date=None):
    sql = """
        SELECT
          p.id,
          p.name,
          p.username,

          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                   OR g.played_at BETWEEN $1 AND $2
              THEN s.goals ELSE 0 END), 0) AS total_goals,

          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                   OR g.played_at BETWEEN $1 AND $2
              THEN s.assists ELSE 0 END), 0) AS total_assists,

          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                   OR g.played_at BETWEEN $1 AND $2
              THEN s.autogoals ELSE 0 END), 0) AS total_autogoals,

          -- очки из колонки points
          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                   OR g.played_at BETWEEN $1 AND $2
              THEN s.points ELSE 0 END), 0) AS total_points,

          -- количество матчей
          COALESCE(COUNT(DISTINCT CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                   OR g.played_at BETWEEN $1 AND $2
              THEN g.id END), 0) AS games_played

        FROM players p
        LEFT JOIN game_player_stats s ON s.player_id = p.id
        LEFT JOIN games g ON g.id = s.game_id
        GROUP BY p.id, p.name, p.username
        ORDER BY total_goals DESC, total_assists DESC;
    """
    async with db_connection() as conn:
        return await conn.fetch(sql, start_date, end_date)


async def get_all_player_totals_assists(start_date=None, end_date=None):
    sql = """
        SELECT
          p.id,
          p.name,
          p.username,

          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                   OR g.played_at BETWEEN $1 AND $2
              THEN s.goals ELSE 0 END), 0) AS total_goals,

          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                   OR g.played_at BETWEEN $1 AND $2
              THEN s.assists ELSE 0 END), 0) AS total_assists,

          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                   OR g.played_at BETWEEN $1 AND $2
              THEN s.autogoals ELSE 0 END), 0) AS total_autogoals,

          -- очки из колонки points
          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                   OR g.played_at BETWEEN $1 AND $2
              THEN s.points ELSE 0 END), 0) AS total_points,

          -- количество матчей
          COALESCE(COUNT(DISTINCT CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                   OR g.played_at BETWEEN $1 AND $2
              THEN g.id END), 0) AS games_played

        FROM players p
        LEFT JOIN game_player_stats s ON s.player_id = p.id
        LEFT JOIN games g ON g.id = s.game_id
        GROUP BY p.id, p.name, p.username
        ORDER BY total_assists DESC, total_goals DESC;
    """
    async with db_connection() as conn:
        return await conn.fetch(sql, start_date, end_date)


async def get_top_players_by_points(start_date=None, end_date=None, overall_pts=False):
    order_by = "total_points DESC, total_goals DESC"
    if overall_pts:
        order_by = "overall_pts DESC, total_points DESC"

    sql = f"""
        SELECT
          p.id,
          p.name,
          p.username,

          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                  OR g.played_at BETWEEN $1 AND $2
              THEN s.goals ELSE 0 END), 0) AS total_goals,

          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                  OR g.played_at BETWEEN $1 AND $2
              THEN s.assists ELSE 0 END), 0) AS total_assists,

          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                  OR g.played_at BETWEEN $1 AND $2
              THEN s.autogoals ELSE 0 END), 0) AS total_autogoals,

          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                  OR g.played_at BETWEEN $1 AND $2
              THEN s.points ELSE 0 END), 0) AS total_points,
        
          COALESCE(SUM(CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                  OR g.played_at BETWEEN $1 AND $2
              THEN s.overall_pts ELSE 0 END), 0) AS overall_pts,

          COALESCE(COUNT(DISTINCT CASE
              WHEN $1::date IS NULL OR $2::date IS NULL
                  OR g.played_at BETWEEN $1 AND $2
              THEN g.id END), 0) AS games_played

        FROM players p
        LEFT JOIN game_player_stats s ON s.player_id = p.id
        LEFT JOIN games g ON g.id = s.game_id
        GROUP BY p.id, p.name, p.username
        ORDER BY {order_by}
    """

    async with db_connection() as conn:
        return await conn.fetch(sql, start_date, end_date)


async def all_chats():
    async with db_connection() as conn:
        sql = """
        SELECT chat_id
        from chats; 
        """
        rows = await conn.fetch(sql)
        return [dict(row) for row in rows]


async def change_players_name(name, player_id):
    async with db_connection() as conn:
        sql = """
        UPDATE players
        SET name = $1
        WHERE id = $2;
        """
        await conn.execute(sql, name, player_id)


async def mark_player_paid(game_id, player_id):
    async with db_connection() as conn:
        await conn.execute("""
            INSERT INTO game_payments (game_id, player_id)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
        """, game_id, player_id)


async def add_summa(game_id, summa):
    async with db_connection() as conn:
        await conn.execute("""
            UPDATE game_payments
            SET summa = $2
            WHERE game_id = $1
        """, game_id, summa)


async def get_paid_players(game_id):
    async with db_connection() as conn:
        rows = await conn.fetch("""
            SELECT players.username FROM game_payments
            JOIN players ON players.id = game_payments.player_id
            WHERE game_payments.game_id = $1
        """, game_id)
        return [r["username"] for r in rows]


async def remove_payment(game_id, player_id):
    async with db_connection() as conn:
        await conn.execute("""
            DELETE FROM game_payments
            WHERE game_id = $1 AND player_id = $2
        """, game_id, player_id)

async def add_summa(game_id, summa):
    async with db_connection() as conn:
        await conn.execute("""
            INSERT INTO game_sums (game_id, summa)
            VALUES ($1, $2)
            ON CONFLICT (game_id) DO UPDATE SET summa = EXCLUDED.summa
        """, game_id, summa)

async def find_summa(game_id):
    async with db_connection() as conn:
        row = await conn.fetchrow("""
            SELECT summa FROM game_sums
            WHERE game_id = $1
        """, game_id)
        return row["summa"] if row else 0


async def add_player_to_game_main(game_id: int, player_id: int):
    async with db_connection() as conn:
        await conn.execute("""
            INSERT INTO game_player_stats (game_id, player_id, joined_at)
            VALUES ($1, $2, NOW())
            ON CONFLICT (game_id, player_id) DO NOTHING
        """, game_id, player_id)

async def remove_player_from_game_main(game_id: int, player_id: int):
    async with db_connection() as conn:
        await conn.execute("""
            DELETE FROM game_player_stats
            WHERE game_id = $1 AND player_id = $2
        """, game_id, player_id)


async def add_player_to_reserve(
    game_id: int,
    player_id: int,
    added_by: int | None = None
):
    async with db_connection() as conn:
        await conn.execute("""
            INSERT INTO game_reserve (game_id, player_id, added_by)
            VALUES ($1, $2, $3)
            ON CONFLICT (game_id, player_id) DO NOTHING
        """, game_id, player_id, added_by)

async def remove_player_from_reserve(game_id: int, player_id: int):
    async with db_connection() as conn:
        await conn.execute("""
            DELETE FROM game_reserve
            WHERE game_id = $1 AND player_id = $2
        """, game_id, player_id)

async def find_reserve_players(game_id: int):
    async with db_connection() as conn:
        rows = await conn.fetch("""
            SELECT
                p.id,
                p.name,
                p.username,
                r.added_at
            FROM game_reserve r
            JOIN players p ON p.id = r.player_id
            WHERE r.game_id = $1
            ORDER BY r.added_at ASC, p.id ASC
        """, game_id)

    return [dict(r) for r in rows]


async def pop_first_from_reserve(game_id: int) -> int | None:
    async with db_connection() as conn:
        row = await conn.fetchrow("""
            SELECT player_id
            FROM game_reserve
            WHERE game_id = $1
            ORDER BY added_at ASC
            LIMIT 1
        """, game_id)

        if not row:
            return None

        player_id = row["player_id"]

        await conn.execute("""
            DELETE FROM game_reserve
            WHERE game_id = $1 AND player_id = $2
        """, game_id, player_id)

    return player_id

async def not_in_reserve_players(game_id):
    async with db_connection() as conn:
        rows = await conn.fetch("""
            SELECT
                p.id,
                p.name,
                p.username
            FROM players p
            WHERE NOT EXISTS (
                SELECT 1 
                FROM game_player_stats s
                WHERE s.game_id = $1
                  AND s.player_id = p.id
            )
            AND NOT EXISTS (
                SELECT 1
                FROM game_reserve r
                WHERE r.game_id = $1
                  AND r.player_id = p.id
            )
            ORDER BY p.name ASC, p.id ASC;
        """, game_id)

    return [dict(r) for r in rows]
