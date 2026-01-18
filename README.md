# BookFlux

BookFlux is an AI book translation pipeline that converts PDF books into other languages (default: French).
Output is a clean, text-only PDF generated from the translated content.

## Features
- Extract text from PDFs with `pdfplumber`
- Optional OCR for scanned PDFs (off by default)
- Optional page break preservation
- Optional soft layout preservation for text PDFs
- Provider-agnostic translation with pluggable adapters
- Chunked translation for large documents (~200 pages)
- Simple CLI workflow
- Architecture notes in `docs/architecture.md`
- Provider strategy notes in `docs/providers.md`
- Performance notes in `docs/optimization.md`

## Requirements
- Python 3.10+
- Provider API key (Gemini uses `GEMINI_API_KEY`)

## Install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage
```bash
export GEMINI_API_KEY="your-key"
python -m bookflux \
  --input /path/to/book.pdf \
  --output /path/to/book.fr.pdf \
  --lang fr \
  --provider gemini
```
You can pass `--api-key` to override the provider's environment variable.
Language codes use ISO/BCP-47 (e.g., `fr`, `pt-BR`) and are expanded to full names in prompts.

### Provider config file
You can store provider settings in a JSON file and keep the CLI shorter.

Example `provider.json`:
```json
{
  "provider": "ollama",
  "model": "llama3.1",
  "base_url": "http://localhost:11434/v1",
  "temperature": 0.2,
  "timeout": 180,
  "max_retries": 3
}
```
`timeout` is in seconds.

Usage:
```bash
python -m bookflux \
  --input /path/to/book.pdf \
  --output /path/to/book.fr.pdf \
  --lang fr \
  --provider-config provider.json
```
You can override the config timeout with `--timeout 180`.

### List available providers
```bash
python -m bookflux --list-providers
```

### List available models
```bash
python -m bookflux --list-models --provider gemini
```

### Use Ollama (local)
```bash
python -m bookflux \
  --input /path/to/book.pdf \
  --output /path/to/book.fr.pdf \
  --lang fr \
  --provider ollama \
  --model llama3.1 \
  --base-url http://localhost:11434/v1
```

### Use LM Studio (local)
```bash
python -m bookflux \
  --input /path/to/book.pdf \
  --output /path/to/book.fr.pdf \
  --lang fr \
  --provider lmstudio \
  --model your-model-id \
  --base-url http://localhost:1234/v1
```

### Use OpenAI-compatible servers (local or remote)
```bash
python -m bookflux \
  --input /path/to/book.pdf \
  --output /path/to/book.fr.pdf \
  --lang fr \
  --provider openai-compat \
  --model your-model-id \
  --base-url http://localhost:8000/v1
```

### Quick test (first chunk only)
```bash
python -m bookflux \
  --input /path/to/book.pdf \
  --output /path/to/book.fr.pdf \
  --lang fr \
  --max-chunks 1
```

### Preserve page breaks
```bash
python -m bookflux \
  --input /path/to/book.pdf \
  --output /path/to/book.fr.pdf \
  --lang fr \
  --preserve-pages
```

### Soft layout preservation (text PDFs only)
```bash
python -m bookflux \
  --input /path/to/book.pdf \
  --output /path/to/book.fr.pdf \
  --lang fr \
  --layout soft
```

### Enable OCR (optional)
```bash
python -m bookflux \
  --input /path/to/scanned.pdf \
  --output /path/to/scanned.fr.pdf \
  --lang fr \
  --ocr \
  --ocr-lang eng
```

## Notes
- OCR requires system binaries: poppler (for `pdf2image`) and tesseract.
- The output PDF does not preserve original layout or images.
- With `--preserve-pages`, each input page starts on a new output page.
- `--layout soft` preserves block positions but may shrink text to fit.
- `--layout soft` does not support OCR.
- For large files, expect multiple API calls and higher cost.
- Local providers may require running servers (Ollama or LM Studio) before use.
