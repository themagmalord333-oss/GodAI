import aiohttp
import asyncio
import json
from typing import Dict, Any
from ai.providers.base import BaseProvider

class GeminiWebClient(BaseProvider):
    def __init__(self, session_path: str):
        super().__init__(session_path)
        self.provider_name = "gemini"
        self.api_key = None

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

    async def generate(self, prompt: str) -> Dict[str, Any]:
        await self.load_session()
        if not self.is_connected:
            raise PermissionError("Gemini Key Missing in storage/sessions/gemini/default.json")
        
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
                    "provider": "gemini"
                }