import asyncio
from database.memory import _execute_query, execute_update
from utils.logger import logger

class TaskTracker:
    @staticmethod
    async def create_task(task_id: str, chat_id: int):
        """Initializes a new tracking session in the DB."""
        await execute_update(
            "INSERT INTO agent_tasks (task_id, chat_id, status) VALUES (?, ?, 'active')", 
            (task_id, chat_id)
        )

    @staticmethod
    async def update_progress(task_id: str, role: str, action: str, percent: int):
        """Updates the live progress bar for the Telegram UI."""
        await execute_update(
            "UPDATE agent_tasks SET current_role=?, current_action=?, progress_percent=? WHERE task_id=?",
            (role, action, percent, task_id)
        )
        logger.info(f"[Task {task_id}] {role}: {action} ({percent}%)")

    @staticmethod
    async def check_intervention(task_id: str) -> str:
        """
        The CEO's Control Hook. Checks if the task is paused.
        If paused, it suspends AI execution until resumed.
        Returns any new instructions appended by the CEO.
        """
        row = await _execute_query(
            "SELECT is_paused, ceo_intervention FROM agent_tasks WHERE task_id=?", 
            (task_id,), fetch_one=True
        )
        if not row: return ""
        
        is_paused, intervention = row
        
        if is_paused:
            logger.info(f"[Task {task_id}] PAUSED by CEO. Holding execution...")
            
        while is_paused:
            await asyncio.sleep(2) # Suspend execution thread
            row = await _execute_query("SELECT is_paused, ceo_intervention FROM agent_tasks WHERE task_id=?", (task_id,), fetch_one=True)
            is_paused = row[0]
            intervention = row[1]
            
        if intervention:
            logger.info(f"[Task {task_id}] CEO injected new instructions: {intervention}")
            # Clear the intervention once read
            await execute_update("UPDATE agent_tasks SET ceo_intervention = NULL WHERE task_id=?", (task_id,))
            return f"\n\n[URGENT UPDATE FROM CEO]: {intervention}"
            
        return ""

    @staticmethod
    async def complete_task(task_id: str):
        await execute_update("UPDATE agent_tasks SET status='completed', progress_percent=100 WHERE task_id=?", (task_id,))