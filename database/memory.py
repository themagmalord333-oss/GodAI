import aiosqlite
from config.config import Config
from utils.logger import logger

async def _execute_query(query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = False):
    try:
        async with aiosqlite.connect(Config.DB_PATH) as db:
            async with db.execute(query, params) as cursor:
                if fetch_one: return await cursor.fetchone()
                if fetch_all: return await cursor.fetchall()
                await db.commit()
                return cursor.lastrowid
    except Exception as e:
        logger.error(f"DB Query Error: {e}")
        return None

async def execute_update(query: str, params: tuple = ()):
    try:
        async with aiosqlite.connect(Config.DB_PATH) as db:
            cursor = await db.execute(query, params)
            await db.commit()
            return cursor.rowcount
    except Exception as e:
        logger.error(f"DB Update Error: {e}")
        return 0

async def create_new_chat(user_id: int, chat_name: str, project_name: str):
    chat_id = await _execute_query(
        "INSERT INTO chats (user_id, chat_name, project_name) VALUES (?, ?, ?)",
        (user_id, chat_name, project_name)
    )
    if chat_id:
        await execute_update("INSERT INTO ai_sessions (chat_id, user_id) VALUES (?, ?)", (chat_id, user_id))
        await execute_update("INSERT INTO agent_states (chat_id) VALUES (?)", (chat_id,))
    return chat_id