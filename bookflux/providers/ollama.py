from __future__ import annotations

import os

from .base import BaseProvider
from .http_utils import get_json, post_json
from .registry import register_provider


class OllamaProvider(BaseProvider):
    ENV_HOST = "OLLAMA_HOST"
    ENV_MODEL = "OLLAMA_MODEL"

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.2,
        timeout: float = 60,
        max_retries: int = 3,
    ) -> None:
        model_name = model_name or os.getenv(self.ENV_MODEL) or ""
        super().__init__(model_name, temperature=temperature, max_retries=max_retries)
        self.base_url = (
            base_url or os.getenv(self.ENV_HOST) or "http://localhost:11434"
        ).rstrip("/")
        self.timeout = timeout

    def _generate(self, prompt: str) -> str:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature},
        }
        data = post_json(url, payload, timeout=self.timeout)
        return data.get("response", "")

    def list_models(self) -> list[str]:
        url = f"{self.base_url}/api/tags"
        data = get_json(url, timeout=self.timeout)
        models = data.get("models", [])
        names = [model.get("name", "") for model in models]
        return sorted([name for name in names if name])


register_provider("ollama", OllamaProvider)
