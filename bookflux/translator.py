from __future__ import annotations

from collections.abc import Iterable

from .providers.base import TranslatorProvider


def chunk_text(text: str, max_chars: int) -> list[str]:
    paragraphs = [p for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
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


class TranslatorFacade:
    def __init__(
        self,
        provider: TranslatorProvider,
        target_lang: str,
    ) -> None:
        self.provider = provider
        self.target_lang = target_lang

    def translate_chunk(self, text: str) -> str:
        return self.provider.translate(text, self.target_lang)

    def translate_chunks(self, chunks: Iterable[str]) -> list[str]:
        return [self.translate_chunk(chunk) for chunk in chunks]
