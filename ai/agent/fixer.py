import asyncio
from ai.router import magma_router
from ai.sandbox.docker_runner import SecureDockerSandbox
from utils.file_manager import FileManager
from utils.agent_logger import AgentLogger
from ai.agent.task_tracker import TaskTracker
from utils.logger import logger

class AutoFixEngine:
    @staticmethod
    async def run_test_and_fix_loop(chat_id: int, project_name: str, entry_point: str, status_msg, task_id: str, max_attempts: int = 5):
        sandbox = SecureDockerSandbox(project_name)
        
        for attempt in range(1, max_attempts + 1):
            await TaskTracker.update_progress(task_id, "SANDBOX", f"Running Test (Attempt {attempt})", 85)
            await status_msg.edit_text(f"🧪 **Sandbox Execution (Attempt {attempt}/{max_attempts})**\nRunning `{entry_point}`...")
            
            # 1. RUN CODE IN DOCKER
            test_result = await sandbox.execute(entry_point)
            
            # 2. SUCCESS CHECK
            if test_result['status'] == 'success':
                await TaskTracker.complete_task(task_id)
                await status_msg.edit_text(f"✅ **Tests Passed in Sandbox!**\n\n```\n{test_result['logs']}\n```\n\n_Project '{project_name}' is fully functional._")
                return True
                
            error_logs = test_result['logs']
            if not error_logs.strip():
                error_logs = "Program exited unexpectedly with no error output."
                
            await status_msg.edit_text(f"⚠️ **Test Failed (Attempt {attempt})**\n```\n{error_logs}\n```\n\nCalling Reviewer AI...")

            # --- MID-TASK CEO INTERVENTION CHECK ---
            intervention = await TaskTracker.check_intervention(task_id)
            ceo_note = intervention if intervention else ""

            # 3. GET PROJECT CONTEXT FOR FIXER
            existing_code = await FileManager.read_project_context(project_name)
            
            # ==========================================
            # ROLE 4: REVIEWER AI (Analyzes the Error)
            # ==========================================
            await TaskTracker.update_progress(task_id, "REVIEWER", "Analyzing Sandbox Crash", 90)
            
            reviewer_ai = await magma_router.get_agent(chat_id, 'reviewer')
            review_prompt = f"""You are the MAGMA Reviewer AI.
The code crashed in the Docker Sandbox.

ERROR LOGS:
{error_logs}

Analyze the logs and explain EXACTLY why it failed. Be brief. Target the Fixer AI."""

            review_res = await reviewer_ai.generate(prompt=review_prompt)
            await AgentLogger.log_task(chat_id, task_id, "REVIEWER", reviewer_ai.provider_name, reviewer_ai.settings['target_model'], review_prompt, review_res['text'], "Failed")
            
            await status_msg.edit_text(f"🔍 **Reviewer ({reviewer_ai.provider_name}) found bug:**\n`{review_res['text'][:150]}...`\n\nHanding over to Fixer AI...")

            # ==========================================
            # ROLE 5: FIXER AI (Generates Patched Files)
            # ==========================================
            await TaskTracker.update_progress(task_id, "FIXER", "Patching Source Code", 95)
            
            fixer_ai = await magma_router.get_agent(chat_id, 'fixer')
            fix_prompt = f"""You are the MAGMA Fixer AI.
REVIEWER'S ANALYSIS: {review_res['text']}
ERROR TRACE: {error_logs}
CURRENT PROJECT FILES: {existing_context}
{ceo_note}

Task: Fix the bug. Output ONLY the files that need to be changed in the strict markdown format:
### filepath/name.py
```python
<fixed code>
```"""

            fix_res = await fixer_ai.generate(prompt=fix_prompt)
            await AgentLogger.log_task(chat_id, task_id, "FIXER", fixer_ai.provider_name, fixer_ai.settings['target_model'], fix_prompt, fix_res['text'], "Fix Applied")

            # 4. SAVE NEW FILES (VCS automatically backs up original files)
            await status_msg.edit_text(f"🛠 **Fixer ({fixer_ai.provider_name}) applying patch...**\nRe-running tests shortly.")
            await FileManager.extract_and_save_files(chat_id, project_name, fix_res['text'])
            
            # The loop continues back to step 1 (Test again!)
            await asyncio.sleep(2) 

        # If loop exhausts all attempts
        await TaskTracker.update_progress(task_id, "SYSTEM", "Max fix attempts reached", 100)
        await status_msg.edit_text(f"❌ **Max fix attempts ({max_attempts}) reached.**\nThe code is still failing in the Sandbox.\n\nUse `/agentlogs` to review the AI team's thought process or use `/rollback` to revert the files.")
        return False