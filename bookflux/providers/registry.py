from __future__ import annotations

import inspect
from typing import Type

from .base import TranslatorProvider


_REGISTRY: dict[str, Type[TranslatorProvider]] = {}


def register_provider(name: str, provider: Type[TranslatorProvider]) -> None:
    key = name.strip().lower()
    if key in _REGISTRY:
        existing = _REGISTRY[key]
        if existing is provider:
            return
        raise ValueError(f"Provider '{key}' is already registered.")
    _REGISTRY[key] = provider


def unregister_provider(name: str) -> None:
    key = name.strip().lower()
    _REGISTRY.pop(key, None)


def create_provider(name: str, **kwargs) -> TranslatorProvider:
    key = name.strip().lower()
    if key not in _REGISTRY:
        raise ValueError(
            f"Unknown provider '{name}'. Available: {', '.join(list_providers())}"
        )
    provider_cls = _REGISTRY[key]
    return provider_cls(**_filter_kwargs(provider_cls, kwargs))


def list_providers() -> list[str]:
    return sorted(_REGISTRY.keys())


def _filter_kwargs(provider_cls: Type[TranslatorProvider], kwargs: dict) -> dict:
    signature = inspect.signature(provider_cls.__init__)
    allowed = set(signature.parameters.keys())
    allowed.discard("self")
    return {key: value for key, value in kwargs.items() if key in allowed}
