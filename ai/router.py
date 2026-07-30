import json
import os
from config import Config
from database.memory import _execute_query
from ai.providers.factory import ProviderFactory
from utils.logger import logger

class AIRouter:
    def __init__(self):
        self.models_config = self._load_models_json()

    def _load_models_json(self) -> dict:
        path = os.path.join(Config.BASE_DIR, "config", "models.json")
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load models.json: {e}")
            return {}

    async def get_agent(self, chat_id: int, role: str):
        """
        Dynamically fetches the exact AI provider and model for a specific role (e.g., 'coder').
        """
        # 1. Fetch CEO's current configuration for this role
        query = f"""
            SELECT 
                {role}_ai, {role}_model, 
                ai_mode, thinking_mode, search_mode, vision_mode 
            FROM ai_sessions WHERE chat_id = ?
        """
        row = await _execute_query(query, (chat_id,), fetch_one=True)
        if not row:
            raise ValueError(f"Team configuration not found for chat {chat_id}")

        provider_name = row[0].lower()
        base_model = row[1]
        
        settings = {
            "mode": row[2],
            "thinking": bool(row[3]),
            "search": bool(row[4]),
            "vision": bool(row[5]),
            "target_model": base_model,
            "role": role.upper()
        }

        # 2. Smart Model Switching (Overriding base model based on CEO Toggles)
        if provider_name in self.models_config:
            p_config = self.models_config[provider_name]
            
            if settings["thinking"] and p_config.get("reasoning"):
                settings["target_model"] = p_config["reasoning"]
            elif settings["mode"] == "instant" and p_config.get("instant"):
                settings["target_model"] = p_config["instant"]
            elif settings["mode"] == "vision" and p_config.get("vision"):
                settings["target_model"] = p_config["vision"]

        # 3. Locate the Cookie/Session
        session_path = os.path.join(Config.SESSIONS_DIR, provider_name, "default.json")

        # 4. Spin up the Provider via Factory
        logger.info(f"[{role.upper()}] Routing to {provider_name.upper()} using {settings['target_model']}")
        
        provider = ProviderFactory.get_provider(provider_name, session_path)
        provider.settings = settings # Inject dynamic settings
        
        return provider

# Global instance
magma_router = AIRouter()