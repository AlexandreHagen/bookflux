from __future__ import annotations

import os

from .base import BaseProvider
from .http_utils import get_json, post_json
from .registry import register_provider


class OpenAICompatProvider(BaseProvider):
    ENV_BASE_URL = "OPENAI_COMPAT_BASE_URL"
    ENV_API_KEY = "OPENAI_COMPAT_API_KEY"
    ENV_MODEL = "OPENAI_COMPAT_MODEL"

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.2,
        request_mode: str = "chat",
        timeout: float = 60,
        max_retries: int = 3,
    ) -> None:
        if not model_name:
            model_name = os.getenv(self.ENV_MODEL) or ""
        super().__init__(model_name, temperature=temperature, max_retries=max_retries)
        self.base_url = _normalize_base_url(
            base_url
            if base_url is not None
            else os.getenv(self.ENV_BASE_URL) or "http://localhost:1234/v1"
        )
        self.api_key = api_key if api_key is not None else os.getenv(self.ENV_API_KEY)
        self.timeout = timeout
        normalized_mode = (request_mode or "chat").strip().lower()
        if normalized_mode not in {"chat", "completion"}:
            raise ValueError("request_mode must be 'chat' or 'completion'.")
        self.request_mode = normalized_mode

    def _generate(self, prompt: str) -> str:
        if self.request_mode == "completion":
            url = f"{self.base_url}/completions"
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "temperature": self.temperature,
                "stream": False,
            }
        else:
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self.temperature,
                "stream": False,
            }
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = post_json(url, payload, headers=headers, timeout=self.timeout)
        choices = data.get("choices", [])
        if not choices:
            return ""
        choice = choices[0]
        if self.request_mode == "completion":
            return choice.get("text", "")
        message = choice.get("message", {})
        if "content" in message:
            return message.get("content", "")
        return choice.get("text", "")

    def list_models(self) -> list[str]:
        url = f"{self.base_url}/models"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        data = get_json(url, headers=headers, timeout=self.timeout)
        models = data.get("data", [])
        return sorted([model["id"] for model in models if model.get("id")])


def _normalize_base_url(base_url: str) -> str:
    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1"):
        return base_url
    return f"{base_url}/v1"


register_provider("openai-compat", OpenAICompatProvider)
