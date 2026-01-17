import pytest

from bookflux.providers import create_provider, list_providers


def test_list_providers_includes_defaults() -> None:
    providers = set(list_providers())
    assert "gemini" in providers
    assert "ollama" in providers
    assert "lmstudio" in providers
    assert "openai-compat" in providers


def test_create_provider_unknown_raises() -> None:
    with pytest.raises(ValueError):
        create_provider("unknown-provider")


def test_create_provider_openai_compat() -> None:
    provider = create_provider(
        "openai-compat",
        model_name="test-model",
        base_url="http://localhost:8000/v1",
    )
    assert provider.model_name == "test-model"


def test_create_provider_ignores_unknown_kwargs() -> None:
    provider = create_provider(
        "openai-compat",
        model_name="local-model",
        base_url="http://localhost:8000/v1",
        unused="ignored",
    )
    assert provider.model_name == "local-model"
