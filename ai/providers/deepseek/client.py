import aiohttp
import asyncio
import json
import time
import uuid
from typing import Dict, Any, Optional
from ai.providers.base import BaseProvider
from utils.logger import logger

class DeepSeekWebClient(BaseProvider):
    def __init__(self, session_path: str):
        super().__init__(session_path)
        self.provider_name = "deepseek"
        self.api_url = "https://chat.deepseek.com/api/v0/chat/completions"
        self.cookies = {}
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
        asyncio.create_task(self.load_session())

    async def load_session(self) -> bool:
        try:
            with open(self.session_path, 'r') as f:
                data = json.load(f)
            
            self.auth_type = data.get("type", "cookie")
            if self.auth_type == "cookie":
                self.cookies = {c["name"]: c["value"] for c in data.get("cookies", [])}
            
            self.user_agent = data.get("user_agent", self.user_agent)
            self.is_connected = bool(self.cookies)
            return self.is_connected
        except Exception as e:
            logger.error(f"DeepSeek Session Load Error: {e}")
            self.is_connected = False
            return False

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "Valid" if self.is_connected else "Invalid",
            "auth_type": self.auth_type,
            "last_sync": time.strftime('%Y-%m-%d %H:%M:%S')
        }

    def _build_payload(self, prompt: str, conv_id: str, parent_id: str) -> dict:
        model = self.settings.get("target_model", "deepseek-coder")
        payload = {
            "message_id": str(uuid.uuid4()),
            "prompt": prompt,
            "model": model,
            "options": {
                "web_search": self.settings.get("search", False),
                "expert_mode": self.settings.get("mode") == "expert"
            }
        }
        if conv_id: payload["chat_session_id"] = conv_id
        if parent_id: payload["parent_message_id"] = parent_id
        return payload

    async def generate(self, prompt: str, conversation_id: Optional[str] = None, parent_id: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_connected:
            raise PermissionError("DeepSeek Cookie missing or expired. Use /addprovider")

        headers = {
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
            "Origin": "https://chat.deepseek.com",
            "Referer": "https://chat.deepseek.com/"
        }
        
        payload = self._build_payload(prompt, conversation_id, parent_id)
        timeout = aiohttp.ClientTimeout(total=60)

        # Retry logic for robust Web Scraping
        for attempt in range(3):
            try:
                async with aiohttp.ClientSession(cookies=self.cookies, headers=headers, timeout=timeout) as session:
                    async with session.post(self.api_url, json=payload) as response:
                        if response.status in [401, 403]:
                            self.is_connected = False
                            raise PermissionError("DeepSeek Unauthorized. Cookie Expired.")
                            
                        response.raise_for_status()
                        data = await response.json()
                        
                        return {
                            "text": data.get("text", data.get("content", "")),
                            "conversation_id": data.get("chat_session_id", conversation_id),
                            "parent_id": data.get("message_id", ""),
                            "provider": "deepseek",
                            "usage": {"input": 0, "output": 0},
                            "timestamp": time.time()
                        }
            except asyncio.TimeoutError:
                if attempt == 2: raise TimeoutError("DeepSeek API timed out.")
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                if attempt == 2 or isinstance(e, PermissionError): raise e
                await asyncio.sleep(2)