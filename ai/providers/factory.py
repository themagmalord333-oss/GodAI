import os
from utils.logger import logger
from ai.providers.base import BaseProvider

def get_deepseek():
    from ai.providers.deepseek.client import DeepSeekWebClient
    return DeepSeekWebClient

def get_chatgpt():
    from ai.providers.chatgpt.client import ChatGPTWebClient
    return ChatGPTWebClient

def get_gemini():
    from ai.providers.gemini.client import GeminiWebClient
    return GeminiWebClient

class ProviderFactory:
    _registry = {
        "deepseek": get_deepseek,
        "chatgpt": get_chatgpt,
        "gemini": get_gemini
    }

    @classmethod
    def get_provider(cls, ai_type: str, session_path: str) -> BaseProvider:
        provider_func = cls._registry.get(ai_type.lower())
        if not provider_func:
            raise ValueError(f"Provider '{ai_type}' is not registered.")
        
        if not os.path.exists(session_path):
            raise FileNotFoundError(f"Missing Session File: {session_path}")
            
        return provider_func()(session_path)