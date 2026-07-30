import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
    
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    PROJECTS_DIR = os.getenv("PROJECTS_DIR", os.path.join(BASE_DIR, "storage", "projects"))
    SESSIONS_DIR = os.getenv("SESSIONS_DIR", os.path.join(BASE_DIR, "storage", "sessions"))
    DB_PATH = os.getenv("DB_PATH", os.path.join(BASE_DIR, "storage", "magma_core.db"))