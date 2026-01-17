from __future__ import annotations

import time
from abc import ABC, abstractmethod

from ..language_utils import language_display_name


class TranslatorProvider(ABC):
    @abstractmethod
    def translate(self, text: str, target_lang: str) -> str:
        raise NotImplementedError

    def list_models(self) -> list[str]:
        return []


class BaseProvider(TranslatorProvider):
    def __init__(
        self,
        model_name: str,
        temperature: float = 0.2,
        max_retries: int = 3,
    ) -> None:
        self.model_name = model_name
        self.temperature = temperature
        self.max_retries = max_retries

    def translate(self, text: str, target_lang: str) -> str:
        if not self.model_name:
            raise ValueError("Missing model name. Provide --model or provider env var.")
        prompt = self.build_prompt(text, target_lang)
        for attempt in range(self.max_retries):
            try:
                return self._generate(prompt).strip()
            except Exception as exc:
                if self._is_not_found(exc):
                    raise ValueError(
                        f"Model '{self.model_name}' not found or unsupported."
                    ) from exc
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2**attempt)
        return ""

    def build_prompt(self, text: str, target_lang: str) -> str:
        target_name = language_display_name(target_lang)
        return (
            f"Translate the following text into {target_name}. "
            "Preserve structure, headings, and line breaks. "
            "Do not add commentary or notes.\n\n"
            f"TEXT:\n{text}"
        )

    def _is_not_found(self, exc: Exception) -> bool:
        message = str(exc).lower()
        return "not found" in message or "404" in message

    @abstractmethod
    def _generate(self, prompt: str) -> str:
        raise NotImplementedError
