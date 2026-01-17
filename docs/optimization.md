# Performance Optimization Notes

This project translates large PDFs chunk by chunk. When using local servers
(LM Studio, Ollama, OpenAI-compatible), most latency often comes from **text
generation**, not prompt processing.

## Observation (LM Studio logs)
LM Studio logs show fast prompt processing but slower generation:
- Prompt processing reaches 100% quickly.
- Generation continues for tens of seconds (completion tokens).

This means the main cost is **output length** and **model speed**, not prompt parsing.

## Prompt Structure (System vs User)
Current requests send a single `user` message:
```json
{
  "messages": [
    { "role": "user", "content": "Translate the following text into French..." }
  ]
}
```
To improve cache reuse and consistency, use a **fixed `system` prompt** plus a
variable `user` message. This makes the static part cache-friendly and reduces
prompt variance.

## Recommended Optimizations

### 1) Limit output tokens
Smaller outputs complete faster.
- Add a `max_output_tokens` (or `max_tokens`) setting for OpenAI-compatible APIs.
- Use conservative values for quick tests, then increase as needed.

### 2) Tune chunk size
Large chunks are slow; tiny chunks are too many calls.
- For local models, start around **1500–2500 characters** and tune by latency.

### 3) Use a stable system prompt
Example concept:
```
System: You are a professional translator. Preserve headings and line breaks.
User: Translate the following text into French (France): ...
```
This improves cache hits (when supported) and keeps behavior consistent.

### 4) Choose a faster model / quantization
Model choice dominates speed:
- Smaller models or lower quantization (Q4/Q5) are significantly faster.
- Prefer speed-optimized variants for large books.

### 5) Avoid aggressive parallelism
Local servers often slow down with too many concurrent requests.
- Sequential or low-concurrency pipelines are usually more stable.

## Planned Flags (if implemented)
- `--system-prompt "..."` to define a fixed system message.
- `--max-output-tokens N` to cap output length.
- Possibly adjust default `--chunk-size` for local providers.

## Practical LM Studio Tips
- Use a model and quantization that fits your hardware comfortably.
- Confirm `/v1/chat/completions` supports `max_tokens` on your setup.
- Monitor token usage; translation outputs are often longer than inputs.
