from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.memory import _execute_query, execute_update
from bot.keyboards import get_ai_settings_kb

router = Router()

# ==========================================
# 1. LIVE TASK INTERVENTION (Pause / Resume)
# ==========================================
@router.callback_query(F.data.startswith("task_"))
async def handle_task_controls(call: CallbackQuery):
    action, task_id = call.data.split("_")[1], call.data.split("_")[2]
    
    if action == "pause":
        await execute_update("UPDATE agent_tasks SET is_paused = 1 WHERE task_id = ?", (task_id,))
        await call.answer("🛑 AI execution PAUSED. Agents are waiting.", show_alert=True)
        
    elif action == "resume":
        await execute_update("UPDATE agent_tasks SET is_paused = 0 WHERE task_id = ?", (task_id,))
        await call.answer("▶️ AI execution RESUMED.", show_alert=True)
        
    elif action == "logs":
        # Quickly fetch the last log for this specific task
        row = await _execute_query(
            "SELECT role, output_response FROM agent_conversations WHERE task_id = ? ORDER BY id DESC LIMIT 1",
            (task_id,), fetch_one=True
        )
        msg = f"Last Action ({row[0]}):\n{row[1][:100]}..." if row else "No actions logged yet."
        await call.answer(msg, show_alert=True)
        
    elif action == "intervene":
        # In a full FSM setup, this would trigger a state waiting for user's text message
        # For simplicity here, we acknowledge the action.
        await call.answer("Reply to the bot with your new instructions!", show_alert=True)
        # Setup FSM logic here to capture the next text and UPDATE agent_tasks SET ceo_intervention = text

# ==========================================
# 2. AI SETTINGS TOGGLES
# ==========================================
@router.callback_query(F.data.startswith("toggle_") | F.data.startswith("mode_"))
async def handle_settings_toggle(call: CallbackQuery):
    parts = call.data.split("_")
    action, value, chat_id = parts[0], parts[1], int(parts[2])
    
    if action == "toggle":
        field = f"{value}_mode" # thinking_mode, search_mode
        await execute_update(f"UPDATE ai_sessions SET {field} = NOT {field} WHERE chat_id = ?", (chat_id,))
    elif action == "mode":
        await execute_update("UPDATE ai_sessions SET ai_mode = ? WHERE chat_id = ?", (value, chat_id))

    # Refresh the UI
    row = await _execute_query(
        "SELECT ai_mode, thinking_mode, search_mode FROM ai_sessions WHERE chat_id = ?", 
        (chat_id,), fetch_one=True
    )
    settings = {"ai_mode": row[0], "thinking_mode": bool(row[1]), "search_mode": bool(row[2])}
    
    await call.message.edit_reply_markup(reply_markup=get_ai_settings_kb(settings, chat_id))
    await call.answer("Settings Updated!")