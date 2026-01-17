from __future__ import annotations

import os
import time
from typing import Iterable, List

from google import genai
from google.genai import types


def chunk_text(text: str, max_chars: int) -> List[str]:
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    chunks: List[str] = []
    current = ""

    for para in paragraphs:
        if len(para) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            start = 0
            while start < len(para):
                chunks.append(para[start : start + max_chars])
                start += max_chars
            continue

        if not current:
            current = para
            continue

        if len(current) + len(para) + 2 <= max_chars:
            current = f"{current}\n\n{para}"
        else:
            chunks.append(current)
            current = para

    if current:
        chunks.append(current)

    return chunks


class Translator:
    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-2.5-flash",
        target_lang: str = "fr",
        temperature: float = 0.2,
        max_retries: int = 3,
    ) -> None:
        api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY.")

        self.model_name = model_name
        self.client = genai.Client(api_key=api_key)
        self.target_lang = target_lang
        self.temperature = temperature
        self.max_retries = max_retries

    def translate_chunk(self, text: str) -> str:
        prompt = (
            f"Translate the following text into {self.target_lang}. "
            "Preserve structure, headings, and line breaks. "
            "Do not add commentary or notes.\n\n"
            f"TEXT:\n{text}"
        )

        for attempt in range(self.max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=self.temperature),
                )
                return (response.text or "").strip()
            except Exception as exc:
                message = str(exc).lower()
                if "not found" in message or "404" in message:
                    raise ValueError(
                        f"Model '{self.model_name}' not found or unsupported. "
                        "Run with --list-models to see available models for this key."
                    ) from exc
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2**attempt)

        return ""

    def translate_chunks(self, chunks: Iterable[str]) -> List[str]:
        outputs: List[str] = []
        for chunk in chunks:
            outputs.append(self.translate_chunk(chunk))
        return outputs
