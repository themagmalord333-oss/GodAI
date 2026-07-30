import aiosqlite
import os
from config import Config
from utils.logger import logger

async def init_db():
    os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
    try:
        async with aiosqlite.connect(Config.DB_PATH) as db:
            # 1. CORE PROJECT & CHATS
            await db.execute('''
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER, chat_name TEXT, project_name TEXT UNIQUE,
                    status TEXT DEFAULT 'active', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 2. THE TEAM CONFIGURATION (Dynamic Roles & Toggles)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS ai_sessions (
                    chat_id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    
                    ai_mode TEXT DEFAULT 'expert',
                    thinking_mode BOOLEAN DEFAULT 0,
                    search_mode BOOLEAN DEFAULT 0,
                    vision_mode BOOLEAN DEFAULT 0,
                    
                    manager_ai TEXT DEFAULT 'gemini', manager_model TEXT DEFAULT 'gemini-1.5-pro',
                    analyzer_ai TEXT DEFAULT 'chatgpt', analyzer_model TEXT DEFAULT 'gpt-4o',
                    planner_ai TEXT DEFAULT 'gemini', planner_model TEXT DEFAULT 'gemini-1.5-pro',
                    coder_ai TEXT DEFAULT 'deepseek', coder_model TEXT DEFAULT 'deepseek-coder',
                    reviewer_ai TEXT DEFAULT 'chatgpt', reviewer_model TEXT DEFAULT 'gpt-4o',
                    fixer_ai TEXT DEFAULT 'deepseek', fixer_model TEXT DEFAULT 'deepseek-reasoner',
                    
                    FOREIGN KEY(chat_id) REFERENCES chats(id) ON DELETE CASCADE
                )
            ''')

            # 3. AI-TO-AI CONVERSATION LOGS (For /agentlogs)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS agent_conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER, task_id TEXT, role TEXT,
                    provider TEXT, model TEXT,
                    input_prompt TEXT, output_response TEXT,
                    status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(chat_id) REFERENCES chats(id) ON DELETE CASCADE
                )
            ''')

            # 4. LIVE TASK TRACKING & CEO INTERVENTION
            await db.execute('''
                CREATE TABLE IF NOT EXISTS agent_tasks (
                    task_id TEXT PRIMARY KEY,
                    chat_id INTEGER,
                    current_role TEXT, current_action TEXT,
                    progress_percent INTEGER DEFAULT 0,
                    is_paused BOOLEAN DEFAULT 0,
                    ceo_intervention TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 5. PROVIDER SESSION MANAGER (Cookie Tracking)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS provider_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT UNIQUE, session_path TEXT,
                    auth_type TEXT, status TEXT DEFAULT 'active'
                )
            ''')
            
            # (Includes standard tables: file_versions, execution_logs, agent_memory, agent_states)
            # Keeping snippet focused on the massive new additions for brevity.
            
            await db.commit()
            logger.info("MAGMA CEO Edition Database Initialized.")
    except Exception as e:
        logger.error(f"DB Init Failed: {e}")
        raise
