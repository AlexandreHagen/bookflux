# Provider Strategy (OpenAI-Compatible Core)

This repository standardizes on a single provider implementation: `openai-compat`.
Local servers such as LM Studio and Ollama expose OpenAI-like APIs, so they can be
handled through one adapter with simple aliases and defaults.

## Decision Summary
- Keep **one core provider**: `openai-compat`.
- Treat `lmstudio` and `ollama` as **aliases** that prefill defaults.
- Remove dedicated provider implementations to reduce maintenance.

## Quick Diagram (Alias Strategy)
```text
CLI
 ├─ --provider openai-compat ───────────────┐
 ├─ --provider lmstudio (alias) ────────────┼─> ProviderFactory
 └─ --provider ollama (alias) ──────────────┘
                                             ↓
                                      OpenAICompatProvider
                                             ↓
                                   /v1/chat/completions
                                   /v1/models
```

## Alias Defaults
- `lmstudio` -> `base_url = http://localhost:1234/v1`
- `ollama`   -> `base_url = http://localhost:11434/v1`

You can still override defaults with CLI flags or `--provider-config`.

## Alias Resolution Rules
- Provider resolution order:
  1) CLI / `--provider-config` values
  2) Alias-specific environment variables
  3) Alias defaults (base URL)
- Alias env vars:
  - `lmstudio`: `LMSTUDIO_MODEL`, `LMSTUDIO_API_KEY`, `LMSTUDIO_BASE_URL`
  - `ollama`: `OLLAMA_MODEL`, `OLLAMA_API_KEY`, `OLLAMA_HOST`
- Aliases always use OpenAI-compatible endpoints (`/v1/chat/completions`, `/v1/models`).

## Options Considered

### Option 1: OpenAI-compat only
- Keep only `openai-compat`.
- Users must always pass the full config.
- Lowest maintenance, less convenience.

### Option 2: Aliases (chosen)
- `openai-compat` is the only implementation.
- `lmstudio` and `ollama` become config aliases.
- Best balance of simplicity and user experience.

### Option 3: Dedicated providers
- Keep separate provider code for each server.
- Potentially richer features, more maintenance and divergence.

## Migration Notes
- Replace:
  - `--provider lmstudio` -> still valid as alias
  - `--provider ollama` -> still valid as alias
- For explicit usage:
  - `--provider openai-compat --base-url http://localhost:1234/v1`
  - `--provider openai-compat --base-url http://localhost:11434/v1`

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
