from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time

class BaseProvider(ABC):
    def __init__(self, session_path: str):
        self.session_path = session_path
        self.is_connected = False
        self.provider_name = "unknown"
        self.auth_type = "unknown"
        self.settings = {} # Injected by the Router

    @abstractmethod
    async def load_session(self) -> bool:
        """Loads cookies/API keys from JSON and validates them."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Returns {"status": "Valid", "model": "...", "auth_type": "cookie"}"""
        pass

    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        conversation_id: Optional[str] = None, 
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes the AI Request.
        MUST RETURN:
        {
            "text": "Generated response...",
            "conversation_id": "remote_id",
            "parent_id": "remote_msg_id",
            "provider": self.provider_name,
            "usage": {"input": int, "output": int},
            "timestamp": float
        }
        """
        pass