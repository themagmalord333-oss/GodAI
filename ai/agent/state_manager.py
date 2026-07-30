from database.memory import execute_update

class AgentStateManager:
    @staticmethod
    async def lock_state(chat_id: int) -> bool:
        affected = await execute_update("UPDATE agent_states SET locked = 1, updated_at = CURRENT_TIMESTAMP WHERE chat_id = ? AND locked = 0", (chat_id,))
        return affected > 0

    @staticmethod
    async def unlock_state(chat_id: int):
        await execute_update("UPDATE agent_states SET locked = 0, status = 'waiting', updated_at = CURRENT_TIMESTAMP WHERE chat_id = ?", (chat_id,))