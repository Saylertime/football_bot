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
                PRIMARY KEY (game_id, player_id)
            );
        """)


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
        print("USERNAME:", username)
        player_id = await conn.fetchrow(sql, username)
        print(player_id, "ID TUT")
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
        SELECT goals, assists from game_player_stats s
        JOIN games g ON g.id = s.game_id
        WHERE player_id = $1 AND game_id = $2 
        """
        stats = await conn.fetchrow(sql, player_id, game_id)
        return stats


async def register_player_in_game(game_id, player_id):
    async with db_connection() as conn:
        await conn.execute(
            """
            INSERT INTO game_player_stats (game_id, player_id, goals, assists)
            VALUES ($1, $2, 0, 0)
            ON CONFLICT (game_id, player_id) DO NOTHING;
            """,
            game_id, player_id
        )


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


async def add_assist(game_id, player_id, count=1):
    async with db_connection() as conn:
        sql = """
        INSERT INTO game_player_stats (game_id, player_id, goals, assists)
        VALUES ($1, $2, 0, $3)
        ON CONFLICT (game_id, player_id) DO UPDATE
          SET assists = game_player_stats.assists + $3;
        """
        await conn.execute(sql, game_id, player_id, count)


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
        WHERE s.player_id IS NULL;
    """
        rows = await conn.fetch(sql, game_id)
        return [dict(row) for row in rows]

async def find_players_in_game(game_id):
    async with db_connection() as conn:
        sql = """
        SELECT
          p.id,
          p.name,
          p.username
        FROM players p
        LEFT JOIN game_player_stats s
          ON s.player_id = p.id
        WHERE game_id = $1
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
              s.assists
            FROM game_player_stats s
            JOIN players p ON p.id = s.player_id
            WHERE s.game_id = $1
            ORDER BY s.goals DESC, s.assists DESC;
            """,
            game_id
        )
        if not rows:
            message = "ℹ️ Для этой игры ещё нет статистики"
            return message

        msg = "Результаты сегодняшних игр: \n\n"
        for num, r in enumerate(rows):
            name = r["name"]
            username = f"@{r['username']}" or ""
            goals = r["goals"]
            assists = r["assists"]
            msg += f"{num + 1}. {name} — {username} | Голов: {goals} | Ассистов: {assists}\n\n"

        return msg


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
          COALESCE(SUM(assists), 0) AS total_assists
        FROM game_player_stats
        WHERE player_id = $1
        """
        row = await conn.fetchrow(sql, player_id)
        return row


async def get_all_player_totals():
    sql = """
    SELECT
      p.id,
      p.name,
      p.username,
      COALESCE(SUM(s.goals),   0) AS total_goals,
      COALESCE(SUM(s.assists), 0) AS total_assists
    FROM players p
    LEFT JOIN game_player_stats s
      ON p.id = s.player_id
    GROUP BY p.id, p.name, p.username
    ORDER BY total_goals DESC, total_assists DESC;
    """
    async with db_connection() as conn:
        rows = await conn.fetch(sql)
        return rows
