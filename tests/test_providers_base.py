import time

import pytest

from bookflux.providers.base import BaseProvider
from bookflux.translator import TranslatorFacade


class StubProvider(BaseProvider):
    def __init__(self, model_name: str = "model", responses=None, max_retries: int = 3):
        super().__init__(model_name, temperature=0.2, max_retries=max_retries)
        self.responses = list(responses or [])
        self.prompts = []
        self.calls = 0

    def _generate(self, prompt: str) -> str:
        self.calls += 1
        self.prompts.append(prompt)
        if self.responses:
            value = self.responses.pop(0)
            if isinstance(value, Exception):
                raise value
            return value
        return "ok"


def test_translate_retries_until_success(monkeypatch) -> None:
    monkeypatch.setattr(time, "sleep", lambda _: None)
    provider = StubProvider(responses=[RuntimeError("temp"), "ok"], max_retries=2)

    result = provider.translate("Hello", "fr")

    assert result == "ok"
    assert provider.calls == 2


def test_translate_raises_on_model_not_found(monkeypatch) -> None:
    monkeypatch.setattr(time, "sleep", lambda _: None)

    class NotFoundError(RuntimeError):
        status_code = 404

    provider = StubProvider(responses=[NotFoundError("not found")], max_retries=1)

    with pytest.raises(ValueError):
        provider.translate("Hello", "fr")


def test_translate_raises_after_max_retries(monkeypatch) -> None:
    monkeypatch.setattr(time, "sleep", lambda _: None)
    provider = StubProvider(responses=[RuntimeError("boom"), RuntimeError("boom")], max_retries=2)

    with pytest.raises(RuntimeError):
        provider.translate("Hello", "fr")


def test_translate_requires_model_name() -> None:
    provider = StubProvider(model_name="")

    with pytest.raises(ValueError):
        provider.translate("Hello", "fr")


def test_translate_builds_prompt_with_language_name() -> None:
    provider = StubProvider(responses=["ok"])

    provider.translate("Hello", "fr")

    assert provider.prompts
    assert "French" in provider.prompts[0]
    assert "TEXT:\nHello" in provider.prompts[0]


def test_translator_facade_translates_chunks() -> None:
    class DummyProvider:
        def __init__(self):
            self.calls = []

        def translate(self, text: str, target_lang: str) -> str:
            self.calls.append((text, target_lang))
            return f"{target_lang}:{text}"

    provider = DummyProvider()
    translator = TranslatorFacade(provider, target_lang="fr")

    assert translator.translate_chunk("hi") == "fr:hi"
    assert translator.translate_chunks(["a", "b"]) == ["fr:a", "fr:b"]
    assert provider.calls == [("hi", "fr"), ("a", "fr"), ("b", "fr")]
