# Architecture (Current)

This document describes the **implemented** BookFlux pipeline for translating PDFs.

## Core Flow

```text
CLI -> Extract -> Chunk -> Translate -> Render
```

### 1) CLI & Configuration
- Entry point: `bookflux/cli.py`.
- Loads optional provider config JSON (`--provider-config`).
- Selects extraction mode:
  - text mode (`pdf_utils.extract_text`)
  - preserve pages (`pdf_utils.normalize_page_texts`)
  - soft layout (`layout_utils.extract_layout_blocks`)
- Builds a provider via the registry and runs translation.

### 2) Text Extraction
- Text PDFs: `pdf_utils.extract_text`.
- OCR path (optional): `ocr_utils.ocr_pdf`.
- Soft layout path: `layout_utils.extract_layout_blocks`.

### 3) Chunking
- `translator.chunk_text` splits content by paragraphs and size limits.
- Chunking happens per document, per page, or per block depending on flags.

### 4) Translation Layer
- `TranslatorFacade` orchestrates translation by delegating to a provider.
- `TranslatorProvider` is the shared interface; `BaseProvider` adds prompt
  construction and retry/backoff around `_generate`.

### 5) Providers & Registry
- Implemented providers:
  - `GeminiProvider`
  - `OpenAICompatProvider`
- Aliases map preset defaults to `OpenAICompatProvider`:
  - `lmstudio` -> `http://localhost:1234/v1`
  - `ollama` -> `http://localhost:11434/v1`

Provider creation is handled in `bookflux/providers/registry.py` and used by the CLI.

## Output Rendering
- `output_utils.write_pdf` renders merged translated text.
- `output_utils.write_pdf_pages` preserves page boundaries.
- `layout_utils.write_pdf_layout` renders into detected text blocks with
  heading-aware sizing and a minimum readable font size.
- Soft layout runs can emit a formatting issue report to summarize truncation or
  font scaling adjustments.
- Soft layout can optionally overflow truncated blocks onto a new page.
- Soft layout can allow extra vertical space before shrinking text.

## Flow Diagram

```text
PDF -> extract_text/extract_layout_blocks -> chunk_text -> TranslatorFacade
     -> Provider (Gemini/OpenAICompat) -> output_utils
```
