import aiosqlite
import os
from config.config import Config
from utils.logger import logger

async def init_db():
    os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
    try:
        async with aiosqlite.connect(Config.DB_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER, chat_name TEXT, project_name TEXT UNIQUE,
                    status TEXT DEFAULT 'active', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS ai_sessions (
                    chat_id INTEGER PRIMARY KEY, user_id INTEGER,
                    ai_mode TEXT DEFAULT 'expert', thinking_mode BOOLEAN DEFAULT 0,
                    search_mode BOOLEAN DEFAULT 0, vision_mode BOOLEAN DEFAULT 0,
                    manager_ai TEXT DEFAULT 'gemini', manager_model TEXT DEFAULT 'gemini-1.5-pro',
                    analyzer_ai TEXT DEFAULT 'chatgpt', analyzer_model TEXT DEFAULT 'gpt-4o',
                    planner_ai TEXT DEFAULT 'gemini', planner_model TEXT DEFAULT 'gemini-1.5-pro',
                    coder_ai TEXT DEFAULT 'deepseek', coder_model TEXT DEFAULT 'deepseek-coder',
                    reviewer_ai TEXT DEFAULT 'chatgpt', reviewer_model TEXT DEFAULT 'gpt-4o',
                    fixer_ai TEXT DEFAULT 'deepseek', fixer_model TEXT DEFAULT 'deepseek-reasoner',
                    FOREIGN KEY(chat_id) REFERENCES chats(id) ON DELETE CASCADE
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS agent_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER, task_id TEXT, role TEXT, provider TEXT, model TEXT,
                    input_prompt TEXT, output_response TEXT, status TEXT, 
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS agent_tasks (
                    task_id TEXT PRIMARY KEY, chat_id INTEGER, current_role TEXT, 
                    current_action TEXT, progress_percent INTEGER DEFAULT 0,
                    is_paused BOOLEAN DEFAULT 0, ceo_intervention TEXT, status TEXT DEFAULT 'active'
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS file_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, project_name TEXT,
                    file_path TEXT, version INTEGER, content TEXT, diff_summary TEXT
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS agent_states (
                    chat_id INTEGER PRIMARY KEY, locked BOOLEAN DEFAULT 0,
                    status TEXT DEFAULT 'waiting', updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            await db.commit()
            logger.info("Database Initialized Successfully.")
    except Exception as e:
        logger.error(f"DB Init Failed: {e}")