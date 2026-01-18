# Performance Optimization Notes (Current State)

This project translates large PDFs chunk by chunk. When using local servers
(LM Studio, Ollama, OpenAI-compatible), most latency often comes from **text
generation**, not prompt processing.

## Observation (LM Studio logs)
LM Studio logs show fast prompt processing but slower generation:
- Prompt processing reaches 100% quickly.
- Generation continues for tens of seconds (completion tokens).

This means the main cost is **output length** and **model speed**, not prompt parsing.

## Prompt Structure (Current)
Requests send a single `user` message:
```json
{
  "messages": [
    { "role": "user", "content": "Translate the following text into French..." }
  ]
}
```

## Existing Controls
- `--chunk-size` controls translation chunk length.
- `--temperature` and `--max-retries` are configurable per provider.
- Requests are sent sequentially (no parallelism).

## Layout Preservation (Current Limitation)
When `--layout soft` is enabled, translations can expand and no longer fit the original
text blocks. The writer attempts to fit text into each block and truncates when the block
is too small, emitting warnings like `text truncated in block at page X`.

Planned optimizations and layout mitigation ideas are tracked locally in
`designing/optimization_backlog.md`.
