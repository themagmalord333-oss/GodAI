import os
from utils.logger import logger
from ai.providers.base import BaseProvider

# Lazy imports to prevent circular dependencies during initialization
def get_deepseek():
    from ai.providers.deepseek.client import DeepSeekWebClient
    return DeepSeekWebClient

def get_chatgpt():
    from ai.providers.chatgpt.client import ChatGPTWebClient
    return ChatGPTWebClient

def get_gemini():
    from ai.providers.gemini.client import GeminiWebClient
    return GeminiWebClient

class SessionCache:
    def __init__(self):
        self._cache = {}

    def get_client(self, provider_class, session_path: str) -> BaseProvider:
        if not os.path.exists(session_path):
            raise FileNotFoundError(f"Missing Session File: {session_path}")
            
        mtime = os.path.getmtime(session_path)
        cache_key = f"{provider_class.__name__}_{session_path}_{mtime}"
        
        if cache_key not in self._cache:
            # Purge stale memory for this specific file
            stale_keys = [k for k in self._cache if k.startswith(f"{provider_class.__name__}_{session_path}")]
            for k in stale_keys:
                del self._cache[k]
                
            self._cache[cache_key] = provider_class(session_path)
            logger.info(f"[ANYSNAP Factory] Instantiated new provider: {cache_key}")
            
        return self._cache[cache_key]

    def purge_provider(self, provider_name: str):
        keys_to_remove = [k for k in self._cache if provider_name.lower() in k.lower()]
        for k in keys_to_remove:
            del self._cache[k]
        logger.info(f"[ANYSNAP Factory] Purged all cache for {provider_name}")

session_manager = SessionCache()

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
            raise ValueError(f"Provider '{ai_type}' is not registered in MAGMA.")
        return session_manager.get_client(provider_func(), session_path)