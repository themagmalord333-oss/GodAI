import uuid
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from config import Config
from database.memory import _execute_query, execute_update, create_new_chat
from bot.keyboards import get_ceo_roles_kb, get_ai_settings_kb, get_live_task_kb
from ai.agent.workflow import AgentWorkflow
from ai.agent.fixer import AutoFixEngine

router = Router()

@router.message(Command("newproject"))
async def cmd_newproject(message: Message):
    """Initialize a new workspace."""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.answer("⚠️ Usage: `/newproject <ProjectName>`", parse_mode="Markdown")
        
    project_name = args[1].strip().replace(" ", "_").lower()
    chat_id = message.chat.id
    
    try:
        await create_new_chat(message.from_user.id, message.chat.full_name, project_name)
        await message.answer(f"✅ **Project `{project_name}` Initialized!**\nWorkspace is ready. Use `/code` to command the AI Team.", parse_mode="Markdown")
    except Exception as e:
        await message.answer("⚠️ Project might already exist or DB error.")

@router.message(Command("roles"))
async def cmd_roles(message: Message):
    """CEO Dashboard to view and manage AI team."""
    chat_id = message.chat.id
    query = """
        SELECT manager_ai, manager_model, analyzer_ai, analyzer_model, 
               planner_ai, planner_model, coder_ai, coder_model, 
               reviewer_ai, reviewer_model, fixer_ai, fixer_model 
        FROM ai_sessions WHERE chat_id = ?
    """
    row = await _execute_query(query, (chat_id,), fetch_one=True)
    if not row:
        return await message.answer("Create a project first using `/newproject`.")

    text = f"""
👑 **MAGMA CEO DASHBOARD - Current Team**

👔 **Head AI:** `{row[0].title()} ({row[1]})`
🧠 **Analyzer:** `{row[2].title()} ({row[3]})`
🏗 **Planner:** `{row[4].title()} ({row[5]})`
💻 **Coder:** `{row[6].title()} ({row[7]})`
🔍 **Reviewer:** `{row[8].title()} ({row[9]})`
🛠 **Fixer:** `{row[10].title()} ({row[11]})`
"""
    await message.answer(text, reply_markup=get_ceo_roles_kb(chat_id), parse_mode="Markdown")

@router.message(Command("agentlogs"))
async def cmd_agentlogs(message: Message):
    """View transparent AI-to-AI communications."""
    chat_id = message.chat.id
    rows = await _execute_query(
        "SELECT role, provider, output_response FROM agent_conversations WHERE chat_id = ? ORDER BY id DESC LIMIT 5",
        (chat_id,), fetch_all=True
    )
    if not rows: return await message.answer("📭 No logs found yet.")
    
    msg = "📜 **LATEST AI TEAM LOGS**\n\n"
    for row in reversed(rows):
        role, provider, response = row
        msg += f"**{role} ({provider.title()})**:\n`{response[:200]}...`\n\n"
    
    await message.answer(msg, parse_mode="Markdown")

@router.message(Command("code"))
async def cmd_code(message: Message):
    """The master trigger: Starts Workflow + Docker Test + Auto-Fix."""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        return await message.answer("⚠️ Usage: `/code <your instructions>`", parse_mode="Markdown")
        
    chat_id = message.chat.id
    prompt = args[1]
    
    # 1. Verify project exists
    project_row = await _execute_query("SELECT project_name FROM chats WHERE id = ?", (chat_id,), fetch_one=True)
    if not project_row:
        return await message.answer("⚠️ No active project. Run `/newproject` first.")
    
    project_name = project_row[0]
    task_id = str(uuid.uuid4())[:8]

    # 2. Provide Live Control UI
    status_msg = await message.answer(
        "🚀 **MAGMA Agency Booting Up...**", 
        reply_markup=get_live_task_kb(task_id),
        parse_mode="Markdown"
    )

    # 3. RUN PIPELINE: Planner -> Coder -> Disk
    await AgentWorkflow.execute_ceo_pipeline(chat_id, project_name, prompt, status_msg)
    
    # 4. RUN PIPELINE: Sandbox -> Reviewer -> Fixer Loop
    # (Assuming main.py as default entrypoint for now. You can make this dynamic later).
    await AutoFixEngine.run_test_and_fix_loop(chat_id, project_name, "main.py", status_msg, task_id)