# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BookFlux is a CLI tool that translates PDF books using LLM providers (Gemini, Ollama, LM Studio, or any OpenAI-compatible API). It extracts text from PDFs, chunks it, translates via a pluggable provider system, and renders output PDFs with optional layout preservation.

## Commands

### Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Run
```bash
python -m bookflux --input book.pdf --output translated.pdf --lang fr --provider gemini
```

### Lint & Format
```bash
ruff check .          # lint
ruff format --check . # format check
ruff check --fix .    # auto-fix lint issues
ruff format .         # auto-format
```

### Tests
```bash
pytest                                          # all tests
pytest tests/test_chunking.py                   # single file
pytest tests/test_chunking.py::test_chunk_text_respects_max_chars  # single test
pytest -v                                       # verbose
```

### Pre-commit
```bash
pre-commit run --all-files
```

## Architecture

### Translation Pipeline

```
PDF → Extract Text/Layout → Chunk → Translate (LLM) → Render Output PDF
```

Three extraction modes controlled by CLI flags:
- **Text-only** (default): `pdf_utils.extract_text()` → reflowed output via `output_utils.write_pdf()`
- **Preserve-pages** (`--preserve-pages`): same extraction, page-aware output via `output_utils.write_pdf_pages()`
- **Soft layout** (`--layout soft`): `layout_utils.extract_layout_blocks()` → block-positioned output via `layout_utils.write_pdf_layout()`, preserving original typography and spatial arrangement

### Provider System

Pluggable provider architecture in `bookflux/providers/`:

- `TranslatorProvider` (ABC): defines `translate(text, target_lang) → str`
- `BaseProvider`: adds prompt building, retry with exponential backoff, model validation
- Concrete providers implement `_generate(prompt) → str`
- `registry.py`: provider registration, alias system, `create_provider()` factory
- **Aliases** (`ollama`, `lmstudio`): preconfigured `OpenAICompatProvider` with default base URLs and env var mappings

To add a new provider: subclass `BaseProvider`, implement `_generate()`, and call `register_provider()`.

### Key Modules

- `cli.py`: argument parsing, config loading (JSON files + CLI overrides), orchestrates the full pipeline
- `translator.py`: `TranslatorFacade` coordinates chunking + provider calls; `chunk_text()` splits by paragraphs respecting max size
- `layout_utils.py`: soft layout mode — block extraction, typography profiling, text fitting into original bounding boxes, formatting issue reporting
- `output_utils.py`: reportlab-based PDF rendering (plain text and page-aware modes)
- `text_utils.py`: line merging heuristics (hyphenation, page numbers, headings)
- `pdf_utils.py`: pdfplumber-based text extraction with line normalization

## Code Conventions

- Python 3.10+ (`from __future__ import annotations` everywhere)
- Ruff for linting and formatting: 100 char line length, Google docstring style
- Dataclasses for data structures (`TextBlock`, `TextLine`, `TypographyProfile`, `FormattingIssue`)
- No external HTTP library — uses stdlib `urllib`
- Type annotations on all functions
- Tests use pytest with `monkeypatch` for mocking; `conftest.py` adds repo root to `sys.path`
