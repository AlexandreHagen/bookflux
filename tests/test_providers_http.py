from bookflux.providers import lmstudio, ollama, openai_compat


def test_ollama_generate_uses_expected_endpoint(monkeypatch) -> None:
    captured = {}

    def fake_post_json(url, payload, headers=None, timeout=None):
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = headers
        captured["timeout"] = timeout
        return {"choices": [{"message": {"content": "ok"}}]}

    monkeypatch.setattr(openai_compat, "post_json", fake_post_json)

    provider = ollama.OllamaProvider(
        model_name="llama3.1",
        base_url="http://localhost:11434",
    )
    result = provider._generate("test prompt")

    assert result == "ok"
    assert captured["url"] == "http://localhost:11434/v1/chat/completions"
    assert captured["payload"]["model"] == "llama3.1"
    assert captured["payload"]["stream"] is False
    assert captured["payload"]["messages"][0]["content"] == "test prompt"


def test_ollama_list_models(monkeypatch) -> None:
    def fake_get_json(url, headers=None, timeout=None):
        assert url == "http://localhost:11434/v1/models"
        return {"data": [{"id": "m1"}, {"id": "m2"}]}

    monkeypatch.setattr(openai_compat, "get_json", fake_get_json)
    provider = ollama.OllamaProvider(model_name="m1", base_url="http://localhost:11434")

    assert provider.list_models() == ["m1", "m2"]


def test_lmstudio_generate_uses_expected_endpoint(monkeypatch) -> None:
    captured = {}

    def fake_post_json(url, payload, headers=None, timeout=None):
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = headers
        captured["timeout"] = timeout
        return {"choices": [{"message": {"content": "ok"}}]}

    monkeypatch.setattr(openai_compat, "post_json", fake_post_json)

    provider = lmstudio.LMStudioProvider(
        model_name="local-model",
        base_url="http://localhost:1234/v1",
        api_key="token",
    )
    result = provider._generate("test prompt")

    assert result == "ok"
    assert captured["url"] == "http://localhost:1234/v1/chat/completions"
    assert captured["payload"]["model"] == "local-model"
    assert captured["headers"]["Authorization"] == "Bearer token"


def test_lmstudio_list_models(monkeypatch) -> None:
    def fake_get_json(url, headers=None, timeout=None):
        assert url == "http://localhost:1234/v1/models"
        return {"data": [{"id": "m1"}, {"id": "m2"}]}

    monkeypatch.setattr(openai_compat, "get_json", fake_get_json)
    provider = lmstudio.LMStudioProvider(model_name="m1", base_url="http://localhost:1234/v1")

    assert provider.list_models() == ["m1", "m2"]


def test_openai_compat_generate_uses_expected_endpoint(monkeypatch) -> None:
    captured = {}

    def fake_post_json(url, payload, headers=None, timeout=None):
        captured["url"] = url
        captured["payload"] = payload
        captured["headers"] = headers
        captured["timeout"] = timeout
        return {"choices": [{"message": {"content": "ok"}}]}

    monkeypatch.setattr(openai_compat, "post_json", fake_post_json)

    provider = openai_compat.OpenAICompatProvider(
        model_name="local-model",
        base_url="http://localhost:8000/v1",
        api_key="token",
    )
    result = provider._generate("test prompt")

    assert result == "ok"
    assert captured["url"] == "http://localhost:8000/v1/chat/completions"
    assert captured["payload"]["model"] == "local-model"
    assert captured["headers"]["Authorization"] == "Bearer token"


def test_openai_compat_list_models(monkeypatch) -> None:
    def fake_get_json(url, headers=None, timeout=None):
        assert url == "http://localhost:8000/v1/models"
        return {"data": [{"id": "m1"}, {"id": "m2"}]}

    monkeypatch.setattr(openai_compat, "get_json", fake_get_json)
    provider = openai_compat.OpenAICompatProvider(
        model_name="m1", base_url="http://localhost:8000/v1"
    )

    assert provider.list_models() == ["m1", "m2"]
