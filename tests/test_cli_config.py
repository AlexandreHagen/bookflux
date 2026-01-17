import json

import pytest

from bookflux import cli as cli_module


def test_load_provider_config(tmp_path) -> None:
    config_path = tmp_path / "provider.json"
    payload = {
        "provider": "ollama",
        "model": "llama3.1",
        "base_url": "http://localhost:11434",
        "temperature": 0.3,
        "max_retries": 2,
    }
    config_path.write_text(json.dumps(payload), encoding="utf-8")

    config = cli_module._load_provider_config(str(config_path))

    assert config["provider"] == "ollama"
    assert config["model"] == "llama3.1"


def test_load_provider_config_missing_raises(tmp_path) -> None:
    with pytest.raises(ValueError):
        cli_module._load_provider_config(str(tmp_path / "missing.json"))


def test_load_provider_config_requires_object(tmp_path) -> None:
    config_path = tmp_path / "bad.json"
    config_path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    with pytest.raises(ValueError):
        cli_module._load_provider_config(str(config_path))


def test_get_float_and_int() -> None:
    config = {"temperature": "0.5", "max_retries": "4"}

    assert cli_module._get_float(config, "temperature", 0.2) == 0.5
    assert cli_module._get_int(config, "max_retries", 3) == 4
