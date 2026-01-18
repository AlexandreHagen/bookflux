from __future__ import annotations

import os

from .openai_compat import OpenAICompatProvider
from .registry import register_provider


class OllamaProvider(OpenAICompatProvider):
    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.2,
        timeout: float = 60,
        max_retries: int = 3,
    ) -> None:
        if model_name is None:
            model_name = os.getenv("OLLAMA_MODEL") or ""
        if api_key is None:
            api_key = os.getenv("OLLAMA_API_KEY")
        if base_url is None:
            base_url = os.getenv("OLLAMA_HOST") or "http://localhost:11434"
        super().__init__(
            model_name=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
            timeout=timeout,
            max_retries=max_retries,
        )


register_provider("ollama", OllamaProvider)
