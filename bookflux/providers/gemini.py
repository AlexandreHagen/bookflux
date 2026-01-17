from __future__ import annotations

import os

from google import genai
from google.genai import types

from .base import BaseProvider
from .registry import register_provider


class GeminiProvider(BaseProvider):
    DEFAULT_MODEL = "gemini-2.5-flash"
    ENV_API_KEY = "GEMINI_API_KEY"

    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
        temperature: float = 0.2,
        max_retries: int = 3,
    ) -> None:
        api_key = api_key or os.getenv(self.ENV_API_KEY)
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY.")

        model_name = model_name or self.DEFAULT_MODEL
        super().__init__(model_name, temperature=temperature, max_retries=max_retries)
        self.client = genai.Client(api_key=api_key)

    def _generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=self.temperature),
        )
        return response.text or ""

    def list_models(self) -> list[str]:
        models = []
        for model in self.client.models.list():
            if not _supports_generate_content(model):
                continue
            name = getattr(model, "name", "")
            if name.startswith("models/"):
                name = name[len("models/") :]
            if name:
                models.append(name)
        return sorted(models)


def _supports_generate_content(model) -> bool:
    methods = (
        getattr(model, "supported_generation_methods", None)
        or getattr(model, "supported_methods", None)
        or getattr(model, "supported_actions", None)
    )
    if not methods:
        return False
    normalized = [str(method).lower() for method in methods]
    return any(
        "generatecontent" in method or "generate_content" in method
        for method in normalized
    )


register_provider("gemini", GeminiProvider)
