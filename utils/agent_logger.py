from database.memory import execute_update
from utils.logger import logger

class AgentLogger:
    @staticmethod
    async def log_task(chat_id: int, task_id: str, role: str, provider: str, model: str, input_prompt: str, output_response: str, status: str = "Completed"):
        try:
            query = """INSERT INTO agent_conversations 
                       (chat_id, task_id, role, provider, model, input_prompt, output_response, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
            await execute_update(query, (chat_id, task_id, role.upper(), provider.upper(), model, input_prompt, output_response, status))
            logger.info(f"[Agent Log] {role.upper()} ({provider}) logged task '{task_id}'.")
        except Exception as e:
            logger.error(f"[Agent Log] Failed to log conversation: {e}")