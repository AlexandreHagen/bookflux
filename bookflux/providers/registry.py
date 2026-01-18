from __future__ import annotations

import inspect
import os
from dataclasses import dataclass
from typing import Type

from .base import TranslatorProvider


_REGISTRY: dict[str, Type[TranslatorProvider]] = {}
_ALIASES: dict[str, "ProviderAlias"] = {}


@dataclass(frozen=True)
class ProviderAlias:
    provider_cls: Type[TranslatorProvider]
    defaults: dict[str, object]
    env_map: dict[str, str]


def register_provider(name: str, provider: Type[TranslatorProvider]) -> None:
    key = name.strip().lower()
    if key in _REGISTRY:
        existing = _REGISTRY[key]
        if existing is provider:
            return
        raise ValueError(f"Provider '{key}' is already registered.")
    _REGISTRY[key] = provider


def register_alias(
    name: str,
    provider_cls: Type[TranslatorProvider],
    defaults: dict[str, object] | None = None,
    env_map: dict[str, str] | None = None,
) -> None:
    key = name.strip().lower()
    alias = ProviderAlias(provider_cls, defaults or {}, env_map or {})
    if key in _ALIASES:
        existing = _ALIASES[key]
        if existing == alias:
            return
        raise ValueError(f"Alias '{key}' is already registered.")
    if key in _REGISTRY:
        raise ValueError(f"Alias '{key}' conflicts with provider registration.")
    _ALIASES[key] = alias


def unregister_provider(name: str) -> None:
    key = name.strip().lower()
    _REGISTRY.pop(key, None)


def create_provider(name: str, **kwargs) -> TranslatorProvider:
    key = name.strip().lower()
    if key in _ALIASES:
        alias = _ALIASES[key]
        provider_cls = alias.provider_cls
        kwargs = _apply_alias(alias, kwargs)
        return provider_cls(**_filter_kwargs(provider_cls, kwargs))
    if key not in _REGISTRY:
        raise ValueError(
            f"Unknown provider '{name}'. Available: {', '.join(list_providers())}"
        )
    provider_cls = _REGISTRY[key]
    return provider_cls(**_filter_kwargs(provider_cls, kwargs))


def list_providers() -> list[str]:
    return sorted({*_REGISTRY.keys(), *_ALIASES.keys()})


def _filter_kwargs(provider_cls: Type[TranslatorProvider], kwargs: dict) -> dict:
    signature = inspect.signature(provider_cls.__init__)
    allowed = set(signature.parameters.keys())
    allowed.discard("self")
    return {key: value for key, value in kwargs.items() if key in allowed}


def _apply_alias(alias: ProviderAlias, kwargs: dict) -> dict:
    resolved = dict(kwargs)
    for key, env_var in alias.env_map.items():
        if resolved.get(key) is None:
            value = os.getenv(env_var)
            if value is not None:
                resolved[key] = value
    for key, default in alias.defaults.items():
        if resolved.get(key) is None:
            resolved[key] = default
    for key in ("model_name", "api_key"):
        if key in alias.env_map and resolved.get(key) is None:
            resolved[key] = ""
    return resolved
