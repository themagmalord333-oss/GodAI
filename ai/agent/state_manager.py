from database.memory import execute_update
from utils.logger import logger

class AgentStateManager:
    @staticmethod
    async def lock_state(chat_id: int) -> bool:
        """Atomic lock. Returns True if successfully locked, False if already busy."""
        # Note: Requires agent_states table to have a row for this chat_id
        affected = await execute_update(
            "UPDATE agent_states SET locked = 1, updated_at = CURRENT_TIMESTAMP WHERE chat_id = ? AND locked = 0",
            (chat_id,)
        )
        return affected > 0

    @staticmethod
    async def unlock_state(chat_id: int):
        """Releases the lock so the bot can accept new commands."""
        await execute_update(
            "UPDATE agent_states SET locked = 0, status = 'waiting', updated_at = CURRENT_TIMESTAMP WHERE chat_id = ?", 
            (chat_id,)
        )