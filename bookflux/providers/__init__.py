from .gemini import GeminiProvider
from .openai_compat import OpenAICompatProvider
from .registry import (
    create_provider,
    list_providers,
    register_alias,
    unregister_provider,
)

register_alias(
    "lmstudio",
    OpenAICompatProvider,
    defaults={"base_url": "http://localhost:1234/v1"},
    env_map={
        "model_name": "LMSTUDIO_MODEL",
        "api_key": "LMSTUDIO_API_KEY",
        "base_url": "LMSTUDIO_BASE_URL",
    },
)
register_alias(
    "ollama",
    OpenAICompatProvider,
    defaults={"base_url": "http://localhost:11434/v1"},
    env_map={
        "model_name": "OLLAMA_MODEL",
        "api_key": "OLLAMA_API_KEY",
        "base_url": "OLLAMA_HOST",
    },
)

__all__ = [
    "GeminiProvider",
    "OpenAICompatProvider",
    "create_provider",
    "list_providers",
    "unregister_provider",
]
