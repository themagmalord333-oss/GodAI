import asyncio
import uuid
from ai.router import magma_router
from ai.agent.task_tracker import TaskTracker
from ai.agent.state_manager import AgentStateManager
from utils.agent_logger import AgentLogger
from utils.file_manager import FileManager
from utils.logger import logger

class AgentWorkflow:
    @staticmethod
    async def execute_ceo_pipeline(chat_id: int, project_name: str, user_prompt: str, status_msg):
        """
        The core pipeline: Manager -> Planner -> Coder.
        (Reviewer and Fixer are hooked via the Sandbox loop later).
        """
        # 1. Acquire Lock
        if not await AgentStateManager.lock_state(chat_id):
            await status_msg.edit_text("⚠️ **An AI task is already running for this project.**")
            return

        task_id = str(uuid.uuid4())[:8]
        await TaskTracker.create_task(task_id, chat_id)
        
        try:
            # ==========================================
            # ROLE 1: MANAGER AI (Breaks down the task)
            # ==========================================
            await TaskTracker.update_progress(task_id, "MANAGER", "Analyzing CEO Request", 10)
            await status_msg.edit_text(f"👔 **Manager AI is analyzing task...**\nProgress: █░░░░░░░░░ 10%")
            
            manager_ai = await magma_router.get_agent(chat_id, 'manager')
            manager_prompt = f"You are the MAGMA Manager AI. The CEO requested: '{user_prompt}'. Briefly outline the required system components to guide the Planner."
            
            manager_res = await manager_ai.generate(prompt=manager_prompt)
            await AgentLogger.log_task(chat_id, task_id, "MANAGER", manager_ai.provider_name, manager_ai.settings['target_model'], manager_prompt, manager_res['text'])

            # --- MID-TASK CEO INTERVENTION CHECK ---
            intervention = await TaskTracker.check_intervention(task_id)
            ceo_note = intervention if intervention else ""

            # ==========================================
            # ROLE 2: PLANNER AI (Designs the Architecture)
            # ==========================================
            await TaskTracker.update_progress(task_id, "PLANNER", "Drafting Architecture", 30)
            await status_msg.edit_text(f"🏗 **Planner AI ({manager_ai.provider_name}) designing architecture...**\nProgress: ███░░░░░░░ 30%")
            
            # Read existing project context so the planner knows what's already there
            existing_context = await FileManager.read_project_context(project_name)
            
            planner_ai = await magma_router.get_agent(chat_id, 'planner')
            planner_prompt = f"""You are the MAGMA Planner AI. 
MANAGER'S INSTRUCTIONS: {manager_res['text']}
EXISTING PROJECT STATE: {existing_context}
{ceo_note}

Task: Design a strict file-by-file blueprint for this request. Do not write full code, just outline the structure and logic for the Coder."""

            planner_res = await planner_ai.generate(prompt=planner_prompt)
            await AgentLogger.log_task(chat_id, task_id, "PLANNER", planner_ai.provider_name, planner_ai.settings['target_model'], planner_prompt, planner_res['text'])
            
            # --- MID-TASK CEO INTERVENTION CHECK ---
            intervention = await TaskTracker.check_intervention(task_id)
            ceo_note = intervention if intervention else ""

            # ==========================================
            # ROLE 3: CODER AI (Generates the Actual Files)
            # ==========================================
            await TaskTracker.update_progress(task_id, "CODER", "Writing Source Code", 60)
            await status_msg.edit_text(f"💻 **Coder AI ({planner_ai.provider_name}) writing files...**\nProgress: ██████░░░░ 60%")
            
            coder_ai = await magma_router.get_agent(chat_id, 'coder')
            coder_prompt = f"""You are the MAGMA Senior Coder AI.
PLANNER'S BLUEPRINT: {planner_res['text']}
EXISTING PROJECT STATE: {existing_context}
{ceo_note}

Task: Generate the complete, production-ready code.
CRITICAL RULE: You MUST output files in this strict markdown format:
### filepath/name.py
```python
<code here>
```"""

            coder_res = await coder_ai.generate(prompt=coder_prompt)
            await AgentLogger.log_task(chat_id, task_id, "CODER", coder_ai.provider_name, coder_ai.settings['target_model'], coder_prompt, coder_res['text'])

            # ==========================================
            # SAVING TO FILE SYSTEM
            # ==========================================
            await TaskTracker.update_progress(task_id, "SYSTEM", "Saving files to disk", 85)
            await status_msg.edit_text(f"💾 **Saving files to project folder...**\nProgress: ████████░░ 85%")
            
            # This automatically backs up old files to DB before overwriting!
            saved_files = await FileManager.extract_and_save_files(chat_id, project_name, coder_res['text'])

            # Complete!
            await TaskTracker.complete_task(task_id)
            file_list = ", ".join(saved_files) if saved_files else "No files parsed."
            await status_msg.edit_text(f"✅ **Task Completed!**\n\n**Modified Files:** {file_list}\nProgress: ██████████ 100%\n\n_Use /agentlogs to see the team's discussion._")
            
            # (Note: From here, the Telegram handler can present the "🧪 Run in Sandbox" button)

        except Exception as e:
            logger.error(f"Workflow Crash: {e}")
            await status_msg.edit_text(f"❌ **Agency Workflow Crashed:**\n`{str(e)}`")
            await execute_update("UPDATE agent_tasks SET status='failed' WHERE task_id=?", (task_id,))
            
        finally:
            # ABSOLUTE GUARANTEE: Never leave the state locked
            await AgentStateManager.unlock_state(chat_id)