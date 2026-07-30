import asyncio
from ai.router import magma_router
from ai.sandbox.docker_runner import SecureDockerSandbox
from utils.file_manager import FileManager
from utils.agent_logger import AgentLogger
from ai.agent.task_tracker import TaskTracker

class AutoFixEngine:
    @staticmethod
    async def run_test_and_fix_loop(chat_id: int, project_name: str, entry_point: str, status_msg, task_id: str, max_attempts: int = 3):
        sandbox = SecureDockerSandbox(project_name)
        
        for attempt in range(1, max_attempts + 1):
            await status_msg.edit_text(f"🧪 **Testing in Sandbox (Attempt {attempt})**...")
            test_result = await sandbox.execute(entry_point)
            
            if test_result['status'] == 'success':
                await status_msg.edit_text(f"✅ **Tests Passed!**\n```\n{test_result['logs']}\n```")
                return True
                
            error_logs = test_result['logs']
            await status_msg.edit_text(f"⚠️ **Crash Detected!**\n```\n{error_logs}\n```\nCalling Reviewer...")
            
            ceo_note = await TaskTracker.check_intervention(task_id)
            existing_context = await FileManager.read_project_context(project_name)
            
            # REVIEWER
            reviewer_ai = await magma_router.get_agent(chat_id, 'reviewer')
            review_res = await reviewer_ai.generate(f"Explain this crash briefly for Fixer AI: {error_logs}")
            
            # FIXER
            fixer_ai = await magma_router.get_agent(chat_id, 'fixer')
            fix_res = await fixer_ai.generate(f"Fix this bug. REVIEW: {review_res['text']}. CONTEXT: {existing_context}. Output strictly as markdown file blocks.")
            
            await FileManager.extract_and_save_files(chat_id, project_name, fix_res['text'])
            await asyncio.sleep(2)
            
        await status_msg.edit_text("❌ **Max fix attempts reached.**")
        return False