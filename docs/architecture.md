# Architecture (multi-provider AI)

This document proposes an architecture to support multiple AI providers
(Gemini, OpenAI, Anthropic, etc.) with a clean, extensible design that keeps
the current CLI pipeline intact.

## Goals
- Add a provider without changing the pipeline core.
- Normalize different APIs behind a single interface.
- Keep chunking, retry, OCR, layout, and PDF logic shared.
- Enable provider selection via CLI (e.g. `--provider gemini`).

## Recommended patterns
- Strategy: a single `TranslatorProvider` interface.
- Adapter: each provider maps its API to that interface.
- Factory + Registry: create providers by name.
- Template Method: shared retry/backoff in a base class.
- Facade: CLI talks to a single facade, not individual providers.

## High-level view

```text
CLI -> Pipeline -> TranslatorFacade -> ProviderFactory -> ProviderAdapter
         |                               ^
         v                               |
     PDF Extract + OCR + Layout      ProviderRegistry
```

## Components

### 1) Common interface (Strategy)
```python
class TranslatorProvider:
    def translate(self, text: str, target_lang: str, **kwargs) -> str:
        raise NotImplementedError
```

### 2) Provider adapters
Each provider implements the shared interface.

```python
class GeminiProvider(TranslatorProvider):
    def translate(self, text: str, target_lang: str, **kwargs) -> str:
        # Call Gemini API and return translated text
        ...
```

### 3) Registry + Factory
```python
ProviderRegistry = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}

def create_provider(name: str, **cfg) -> TranslatorProvider:
    return ProviderRegistry[name](**cfg)
```

### 4) Template Method (optional but useful)
```python
class BaseProvider(TranslatorProvider):
    def translate(self, text: str, target_lang: str, **kwargs) -> str:
        # Shared retry + backoff + logging
        return self._call_api(text, target_lang, **kwargs)

    def _call_api(self, text: str, target_lang: str, **kwargs) -> str:
        raise NotImplementedError
```

### 5) Translation facade
The CLI talks to a single facade.
```python
class TranslatorFacade:
    def __init__(self, provider: TranslatorProvider):
        self.provider = provider

    def translate(self, text: str, target_lang: str, **kwargs) -> str:
        return self.provider.translate(text, target_lang, **kwargs)
```

## Processing flow (text PDF)

```text
PDF -> extract_text -> chunk_text -> translate (provider) -> write_pdf
```

## Processing flow (soft layout)

```text
PDF -> extract_layout_blocks -> translate per block -> write_pdf_layout
```

## Sequence diagram (simplified)

```text
CLI
 |  parse args
 v
Pipeline
 |  extract text / layout
 |  chunk text
 v
TranslatorFacade
 |  translate(...)
 v
ProviderAdapter (Gemini/OpenAI/Anthropic)
 |  call API
 v
Translated output -> PDF
```

## Class diagram (Mermaid)

```mermaid
classDiagram
    class TranslatorFacade {
        +translate(text, target_lang, **kwargs) str
    }
    class TranslatorProvider {
        +translate(text, target_lang, **kwargs) str
    }
    class BaseProvider {
        +translate(text, target_lang, **kwargs) str
        +_call_api(text, target_lang, **kwargs) str
    }
    class GeminiProvider
    class OpenAIProvider
    class AnthropicProvider
    class ProviderFactory {
        +create(name, **cfg) TranslatorProvider
    }

    TranslatorFacade --> TranslatorProvider
    TranslatorProvider <|-- BaseProvider
    BaseProvider <|-- GeminiProvider
    BaseProvider <|-- OpenAIProvider
    BaseProvider <|-- AnthropicProvider
    ProviderFactory ..> TranslatorProvider
```

## Flow diagram (Mermaid)

```mermaid
flowchart LR
    A[CLI] --> B[PDF Extraction]
    B --> C[Chunking]
    C --> D[TranslatorFacade]
    D --> E[ProviderFactory]
    E --> F[ProviderAdapter]
    F --> G[Provider API]
    G --> H[Translated Text]
    H --> I[PDF Output]
```

## Design notes
- Providers should be as stateless as possible.
- Chunking remains shared across providers.
- Errors and retries live in the base class.
- Provider selection is configuration-driven (CLI/env).

## Future extensions
- Plugin system (entry points) for external providers.
- Translation cache per chunk.
- Batch mode with provider rate limits.
- Crash recovery and resume:
  - Persist a job state (JSON/SQLite) with page/chunk progress and translations.
  - Resume from the last successful chunk without re-translating.
  - Rebuild the final PDF from stored translated chunks on resume.

## Crash Recovery: Analysis and Plan

### Analysis
- Long-running translations are fragile; a single failure can waste time and cost.
- PDF output is not safely appendable in a resumable way; rebuilding from saved chunks is safer.
- A checkpoint must capture enough context to avoid mismatches (input hash, provider config).

### Plan
- Define a checkpoint schema (JSON or SQLite) with:
  - input file hash, provider name, model, and translation settings
  - page index, block/chunk index, and translated text
- Add CLI flags:
  - `--checkpoint PATH` to save progress
  - `--resume` to skip completed work
- On resume:
  - load checkpoint, validate input hash/config
  - continue from the last completed chunk
  - rebuild output PDF from stored translations
- Add tests for:
  - checkpoint write/read
  - resume skipping logic
  - PDF rebuild from saved chunks

## Layout Heuristics: Analysis and Plan

### Analysis
- Extracted PDF text often loses semantic structure (titles, paragraphs, footers).
- Page breaks split sentences and hyphenation, causing unreadable translations.
- Layout blocks need consistent styling to preserve visual hierarchy.

### Plan
- Define a layout classifier per line/block:
  - heading (all caps, larger font size, short length)
  - paragraph (sentence-like, mixed case)
  - footer/page number (short, numeric, low y-position)
- Normalize lines within blocks:
  - merge soft line breaks when the next line starts lowercase
  - keep explicit blank lines as hard paragraph breaks
  - merge hyphenated words across line/page breaks by consuming only the next token
- Preserve hierarchy in output:
  - map headings to a larger font size and extra spacing
  - keep paragraph spacing consistent
  - avoid merging across detected footers/headers
- Add tests for:
  - heading detection and spacing
  - page number/footer skipping
  - hyphen merge with remainder preserved
