from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time

class BaseProvider(ABC):
    def __init__(self, session_path: str):
        self.session_path = session_path
        self.is_connected = False
        self.provider_name = "unknown"
        self.auth_type = "unknown"
        self.settings = {} 

    @abstractmethod
    async def load_session(self) -> bool:
        pass

    @abstractmethod
    async def generate(self, prompt: str) -> Dict[str, Any]:
        pass