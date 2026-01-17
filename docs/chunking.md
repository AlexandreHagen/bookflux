# Chunking Strategy

This project splits extracted text into translation-sized chunks before
sending it to a provider. The current implementation is in
`bookflux/translator.py` (`chunk_text`).

## How it works
- Text is first split into paragraphs using blank lines (`\n\n`).
- Empty paragraphs are dropped.
- Paragraphs are accumulated into a chunk until the total size would exceed
  `max_chars` (character count, not tokens).
- If a single paragraph is longer than `max_chars`, it is split into fixed-size
  slices (no sentence awareness).
- Chunks preserve paragraph separators with double newlines.

## Example

Input (paragraphs):
```
Para A

Para B (long)
```

Output (max_chars small):
```
Chunk 1: "Para A"
Chunk 2: "Para B (slice 1)"
Chunk 3: "Para B (slice 2)"
```

## Where chunking happens
- Default text mode: full document is merged, then chunked.
- `--preserve-pages`: each page is chunked independently.
- `--layout soft`: each text block is chunked independently.

## Current trade-offs
- Fast and predictable, but not sentence-aware.
- Very long paragraphs can be split mid-sentence.
- Chunk size impacts latency and translation quality.

## Future improvements (ideas)
- Sentence-aware chunking (prefer ending at `.?!`).
- Hard limits by token count for better provider control.
- Optional overlap between chunks to reduce context loss.
