import aiohttp
import asyncio
import json
import time
import uuid
from typing import Dict, Any, Optional
from ai.providers.base import BaseProvider
from utils.logger import logger

class ChatGPTWebClient(BaseProvider):
    def __init__(self, session_path: str):
        super().__init__(session_path)
        self.provider_name = "chatgpt"
        self.api_url = "https://chatgpt.com/backend-api/conversation"
        self.access_token = None
        
        asyncio.create_task(self.load_session())

    async def load_session(self) -> bool:
        try:
            with open(self.session_path, 'r') as f:
                data = json.load(f)
            self.access_token = data.get("access_token")
            self.auth_type = "api_token"
            self.is_connected = bool(self.access_token)
            return self.is_connected
        except Exception:
            self.is_connected = False
            return False

    async def health_check(self) -> Dict[str, Any]:
        return {"status": "Valid" if self.is_connected else "Invalid", "auth_type": self.auth_type}

    async def generate(self, prompt: str, conversation_id: Optional[str] = None, parent_id: Optional[str] = None) -> Dict[str, Any]:
        if not self.is_connected:
            raise PermissionError("ChatGPT Token Missing.")

        model = self.settings.get("target_model", "gpt-4o")
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        msg_id = str(uuid.uuid4())
        payload = {
            "action": "next",
            "messages": [{"id": msg_id, "author": {"role": "user"}, "content": {"content_type": "text", "parts": [prompt]}}],
            "model": model,
            "parent_message_id": parent_id or str(uuid.uuid4()),
        }
        if conversation_id: payload["conversation_id"] = conversation_id

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.post(self.api_url, json=payload) as response:
                response.raise_for_status()
                stream_data = await response.text()
                
                # SSE Parser
                full_text, new_conv_id, new_msg_id = "", conversation_id, ""
                for line in stream_data.splitlines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            data = json.loads(line[6:])
                            if "message" in data and data["message"]["author"]["role"] == "assistant":
                                full_text = data["message"]["content"].get("parts", [""])[0]
                                new_msg_id = data["message"]["id"]
                                new_conv_id = data.get("conversation_id", new_conv_id)
                        except json.JSONDecodeError:
                            pass

                return {
                    "text": full_text,
                    "conversation_id": new_conv_id,
                    "parent_id": new_msg_id,
                    "provider": "chatgpt",
                    "usage": {"input": 0, "output": 0},
                    "timestamp": time.time()
                }