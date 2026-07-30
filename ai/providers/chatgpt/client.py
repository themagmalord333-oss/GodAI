import aiohttp
import asyncio
import json
import time
from typing import Dict, Any
from ai.providers.base import BaseProvider

class DeepSeekWebClient(BaseProvider):
    def __init__(self, session_path: str):
        super().__init__(session_path)
        self.provider_name = "deepseek"
        self.api_url = "https://chat.deepseek.com/api/v0/chat/completions"
        self.cookies = {}
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
    async def load_session(self) -> bool:
        try:
            with open(self.session_path, 'r') as f:
                data = json.load(f)
            self.cookies = {c["name"]: c["value"] for c in data.get("cookies", [])}
            self.user_agent = data.get("user_agent", self.user_agent)
            self.is_connected = bool(self.cookies)
            return self.is_connected
        except Exception:
            self.is_connected = False
            return False

    async def generate(self, prompt: str) -> Dict[str, Any]:
        await self.load_session()
        if not self.is_connected:
            raise PermissionError("DeepSeek Cookie missing or invalid in storage/sessions/deepseek/default.json")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
            "Origin": "https://chat.deepseek.com",
            "Referer": "https://chat.deepseek.com/"
        }
        
        payload = {
            "message_id": "auto",
            "prompt": prompt,
            "model": self.settings.get("target_model", "deepseek-coder"),
            "options": {"web_search": self.settings.get("search", False)}
        }

        async with aiohttp.ClientSession(cookies=self.cookies, headers=headers) as session:
            async with session.post(self.api_url, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                return {
                    "text": data.get("text", data.get("content", "")),
                    "provider": "deepseek"
                }