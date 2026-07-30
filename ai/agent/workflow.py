import asyncio
from ai.router import magma_router
from ai.agent.task_tracker import TaskTracker
from ai.agent.state_manager import AgentStateManager
from utils.agent_logger import AgentLogger
from utils.file_manager import FileManager
from utils.logger import logger

class AgentWorkflow:
    @staticmethod
    async def execute_ceo_pipeline(chat_id: int, project_name: str, user_prompt: str, status_msg, task_id: str):
        if not await AgentStateManager.lock_state(chat_id):
            await status_msg.edit_text("⚠️ **An AI task is already running.**")
            return

        await TaskTracker.create_task(task_id, chat_id)
        
        try:
            # 1. MANAGER
            await TaskTracker.update_progress(task_id, "MANAGER", "Analyzing Request", 10)
            manager_ai = await magma_router.get_agent(chat_id, 'manager')
            manager_prompt = f"You are MAGMA Manager AI. Request: '{user_prompt}'. Give a brief architecture outline."
            manager_res = await manager_ai.generate(prompt=manager_prompt)
            await AgentLogger.log_task(chat_id, task_id, "MANAGER", manager_ai.provider_name, manager_ai.settings['target_model'], manager_prompt, manager_res['text'])
            await status_msg.edit_text(f"👔 **Manager ({manager_ai.provider_name}) Planning...**\nProgress: 20%")

            ceo_note = await TaskTracker.check_intervention(task_id)

            # 2. PLANNER
            await TaskTracker.update_progress(task_id, "PLANNER", "Drafting Blueprint", 30)
            existing_context = await FileManager.read_project_context(project_name)
            planner_ai = await magma_router.get_agent(chat_id, 'planner')
            planner_prompt = f"You are Planner AI. MANAGER: {manager_res['text']}. CONTEXT: {existing_context}. {ceo_note}. Give a strict file-by-file blueprint."
            planner_res = await planner_ai.generate(prompt=planner_prompt)
            await AgentLogger.log_task(chat_id, task_id, "PLANNER", planner_ai.provider_name, planner_ai.settings['target_model'], planner_prompt, planner_res['text'])
            await status_msg.edit_text(f"🏗 **Planner ({planner_ai.provider_name}) Drafting...**\nProgress: 40%")

            ceo_note = await TaskTracker.check_intervention(task_id)

            # 3. CODER
            await TaskTracker.update_progress(task_id, "CODER", "Writing Code", 60)
            coder_ai = await magma_router.get_agent(chat_id, 'coder')
            coder_prompt = f"You are Coder AI. PLANNER: {planner_res['text']}. CONTEXT: {existing_context}. {ceo_note}. Output files strictly as:\n### filepath.py\n```python\ncode\n```"
            coder_res = await coder_ai.generate(prompt=coder_prompt)
            await AgentLogger.log_task(chat_id, task_id, "CODER", coder_ai.provider_name, coder_ai.settings['target_model'], coder_prompt, coder_res['text'])
            await status_msg.edit_text(f"💻 **Coder ({coder_ai.provider_name}) Writing Files...**\nProgress: 80%")

            # SAVE
            await TaskTracker.update_progress(task_id, "SYSTEM", "Saving", 90)
            saved_files = await FileManager.extract_and_save_files(chat_id, project_name, coder_res['text'])

            await TaskTracker.complete_task(task_id)
            await status_msg.edit_text(f"✅ **Generation Complete!**\nFiles: {', '.join(saved_files)}")

        except Exception as e:
            logger.error(f"Workflow Crash: {e}")
            await status_msg.edit_text(f"❌ **Agency Crashed:** `{e}`")
        finally:
            await AgentStateManager.unlock_state(chat_id)