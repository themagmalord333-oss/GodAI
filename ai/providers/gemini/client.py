import aiohttp
import asyncio
import json
import time
from typing import Dict, Any, Optional
from ai.providers.base import BaseProvider

class GeminiWebClient(BaseProvider):
    def __init__(self, session_path: str):
        super().__init__(session_path)
        self.provider_name = "gemini"
        self.api_key = None
        asyncio.create_task(self.load_session())

    async def load_session(self) -> bool:
        try:
            with open(self.session_path, 'r') as f:
                data = json.load(f)
            self.api_key = data.get("api_key")
            self.is_connected = bool(self.api_key)
            return self.is_connected
        except Exception:
            self.is_connected = False
            return False

    async def health_check(self) -> Dict[str, Any]:
        return {"status": "Valid" if self.is_connected else "Invalid"}

    async def generate(self, prompt: str, conversation_id: Optional[str] = None, parent_id: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_connected: raise PermissionError("Gemini Session Missing.")
        
        model = self.settings.get("target_model", "gemini-1.5-pro")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        
        payload = {"contents": [{"parts":[{"text": prompt}]}]}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return {
                    "text": text,
                    "conversation_id": conversation_id or "gemini_thread",
                    "parent_id": "none",
                    "provider": "gemini",
                    "usage": {"input": 0, "output": 0},
                    "timestamp": time.time()
                }