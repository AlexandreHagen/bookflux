# Providers (Current)

BookFlux supports multiple AI backends through a shared provider interface.

## Implemented Providers
- `gemini`: Google Gemini API integration.
- `openai-compat`: OpenAI-compatible HTTP API (works with local servers).

## Aliases (Presets for OpenAI-Compatible Servers)
Aliases map to `openai-compat` with defaults:
- `lmstudio` -> `base_url = http://localhost:1234/v1`
- `ollama`   -> `base_url = http://localhost:11434/v1`

You can override any default with CLI flags or `--provider-config`.

## Request Mode (OpenAI-Compatible)
OpenAI-compatible providers can use either:
- `chat` (default): `/v1/chat/completions`
- `completion`: `/v1/completions`

Set it via `--request-mode completion` or in `provider.json`.

## Environment Variables
Aliases support the following environment variables:
- `lmstudio`: `LMSTUDIO_MODEL`, `LMSTUDIO_API_KEY`, `LMSTUDIO_BASE_URL`
- `ollama`: `OLLAMA_MODEL`, `OLLAMA_API_KEY`, `OLLAMA_HOST`

## Example Config (Alias)
```json
{
  "provider": "lmstudio",
  "model": "your-model-id",
  "base_url": "http://localhost:1234/v1",
  "temperature": 0.2,
  "timeout": 180,
  "max_retries": 3
}
```
