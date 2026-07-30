from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_ceo_roles_kb(chat_id: int):
    """Buttons to change which AI handles which role."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👑 Change Head AI", callback_data=f"role_manager_{chat_id}")],
        [
            InlineKeyboardButton(text="🏗 Planner", callback_data=f"role_planner_{chat_id}"),
            InlineKeyboardButton(text="💻 Coder", callback_data=f"role_coder_{chat_id}")
        ],
        [
            InlineKeyboardButton(text="🔍 Reviewer", callback_data=f"role_reviewer_{chat_id}"),
            InlineKeyboardButton(text="🛠 Fixer", callback_data=f"role_fixer_{chat_id}")
        ]
    ])

def get_ai_settings_kb(settings: dict, chat_id: int):
    """Dynamic toggles for AI capabilities."""
    m_inst = "✅" if settings['ai_mode'] == 'instant' else "⬛"
    m_exp = "✅" if settings['ai_mode'] == 'expert' else "⬛"
    
    t_think = "🟢" if settings['thinking_mode'] else "🔴"
    t_search = "🟢" if settings['search_mode'] else "🔴"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"{m_inst} ⚡ Instant", callback_data=f"mode_instant_{chat_id}"),
            InlineKeyboardButton(text=f"{m_exp} 💎 Expert", callback_data=f"mode_expert_{chat_id}")
        ],
        [
            InlineKeyboardButton(text=f"🧠 Deep Think: {t_think}", callback_data=f"toggle_think_{chat_id}"),
            InlineKeyboardButton(text=f"🌐 Web Search: {t_search}", callback_data=f"toggle_search_{chat_id}")
        ]
    ])

def get_live_task_kb(task_id: str):
    """The control panel shown during active AI generation."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛑 Pause AI", callback_data=f"task_pause_{task_id}"),
            InlineKeyboardButton(text="▶️ Resume AI", callback_data=f"task_resume_{task_id}")
        ],
        [InlineKeyboardButton(text="✍️ Give Instruction (Intervene)", callback_data=f"task_intervene_{task_id}")],
        [InlineKeyboardButton(text="📜 Live Agent Logs", callback_data=f"task_logs_{task_id}")]
    ])