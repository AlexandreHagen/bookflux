# BookFlux

BookFlux is an AI book translation pipeline that converts PDF books into other languages (default: French).
Output is a clean, text-only PDF generated from the translated content.

## Features
- Extract text from PDFs with `pdfplumber`
- Optional OCR for scanned PDFs (off by default)
- Optional page break preservation
- Optional soft layout preservation for text PDFs
- Chunked translation for large documents (~200 pages)
- Simple CLI workflow
 - Architecture notes in `docs/architecture.md`

## Requirements
- Python 3.10+
- Gemini API key in `GEMINI_API_KEY`

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
  --model gemini-2.5-flash
```

### List available models
```bash
python -m bookflux --list-models
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
