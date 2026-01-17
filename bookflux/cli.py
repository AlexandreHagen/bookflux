from __future__ import annotations

import argparse
import os
import sys

from google import genai

from .layout_utils import TextBlock, extract_layout_blocks, write_pdf_layout
from .output_utils import write_pdf, write_pdf_pages
from .pdf_utils import extract_text
from .translator import Translator, chunk_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Translate a PDF book using Gemini (default target: French)."
    )
    parser.add_argument("--input", help="Path to input PDF.")
    parser.add_argument("--output", help="Path to output PDF.")
    parser.add_argument("--lang", default="fr", help="Target language code.")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model name.")
    parser.add_argument("--chunk-size", type=int, default=4000, help="Max chars per chunk.")
    parser.add_argument("--temperature", type=float, default=0.2, help="Model temperature.")
    parser.add_argument("--max-retries", type=int, default=3, help="Retries per chunk.")
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=0,
        help="Translate only the first N chunks for quick tests (0 = no limit).",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available Gemini models for your API key and exit.",
    )
    parser.add_argument(
        "--layout",
        choices=["none", "soft"],
        default="none",
        help="Preserve layout softly by reflowing text in detected blocks.",
    )
    parser.add_argument("--ocr", action="store_true", help="Enable OCR for scanned PDFs.")
    parser.add_argument("--ocr-lang", default="eng", help="OCR language code.")
    parser.add_argument(
        "--preserve-pages",
        action="store_true",
        help="Start each translated page on a new output page.",
    )
    return parser


def _supports_generate_content(model) -> bool:
    methods = (
        getattr(model, "supported_generation_methods", None)
        or getattr(model, "supported_methods", None)
        or getattr(model, "supported_actions", None)
    )
    if not methods:
        return False
    normalized = [str(method).lower() for method in methods]
    return any(
        "generatecontent" in method or "generate_content" in method
        for method in normalized
    )


def list_models() -> None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY.")
    client = genai.Client(api_key=api_key)
    models = []
    for model in client.models.list():
        if not _supports_generate_content(model):
            continue
        name = getattr(model, "name", "")
        if name.startswith("models/"):
            name = name[len("models/") :]
        if name:
            models.append(name)

    if not models:
        print("No models available for generateContent.", file=sys.stderr)
        return

    for name in sorted(models):
        print(name)


def main() -> None:
    args = build_parser().parse_args()

    if args.list_models:
        list_models()
        return
    if not args.input or not args.output:
        raise ValueError("Missing required arguments: --input and --output.")

    if args.layout == "soft":
        if args.ocr:
            raise ValueError("Soft layout does not support OCR yet.")

        page_sizes, pages_blocks = extract_layout_blocks(args.input)
        translator = Translator(
            model_name=args.model,
            target_lang=args.lang,
            temperature=args.temperature,
            max_retries=args.max_retries,
        )
        translated_pages: list[list[TextBlock]] = []
        remaining_chunks = args.max_chunks if args.max_chunks > 0 else None

        for page_index, blocks in enumerate(pages_blocks, start=1):
            if remaining_chunks is not None and remaining_chunks <= 0:
                print("Max chunks reached. Stopping early.", file=sys.stderr)
                break
            translated_blocks: list[TextBlock] = []
            for block_index, block in enumerate(blocks, start=1):
                if remaining_chunks is not None and remaining_chunks <= 0:
                    print("Max chunks reached. Stopping early.", file=sys.stderr)
                    break
                block_chunks = chunk_text(block.text, args.chunk_size)
                if not block_chunks:
                    translated_blocks.append(block)
                    continue
                if remaining_chunks is not None and remaining_chunks < len(block_chunks):
                    block_chunks = block_chunks[:remaining_chunks]
                total_chunks = len(block_chunks)
                translated_chunks = []
                for chunk_index, chunk in enumerate(block_chunks, start=1):
                    print(
                        f"Translating page {page_index}/{len(pages_blocks)} "
                        f"block {block_index}/{len(blocks)} "
                        f"(chunk {chunk_index}/{total_chunks})...",
                        file=sys.stderr,
                    )
                    translated_chunks.append(translator.translate_chunk(chunk))
                    if remaining_chunks is not None:
                        remaining_chunks -= 1
                translated_text = "\n\n".join(translated_chunks)
                translated_blocks.append(
                    TextBlock(
                        text=translated_text,
                        x0=block.x0,
                        x1=block.x1,
                        top=block.top,
                        bottom=block.bottom,
                        font_size=block.font_size,
                    )
                )
            translated_pages.append(translated_blocks)
            if remaining_chunks is not None and remaining_chunks <= 0:
                print("Max chunks reached. Stopping early.", file=sys.stderr)
                break

        page_sizes = page_sizes[: len(translated_pages)]
        write_pdf_layout(translated_pages, page_sizes, args.output)
        return

    page_texts = extract_text(
        args.input, use_ocr=args.ocr, ocr_lang=args.ocr_lang
    )
    translator = Translator(
        model_name=args.model,
        target_lang=args.lang,
        temperature=args.temperature,
        max_retries=args.max_retries,
    )

    if args.preserve_pages:
        translated_pages = []
        total_pages = len(page_texts)
        remaining_chunks = args.max_chunks if args.max_chunks > 0 else None
        for page_index, page_text in enumerate(page_texts, start=1):
            if remaining_chunks is not None and remaining_chunks <= 0:
                print("Max chunks reached. Stopping early.", file=sys.stderr)
                break
            page_chunks = chunk_text(page_text, args.chunk_size)
            if not page_chunks:
                translated_pages.append("")
                continue
            if remaining_chunks is not None and remaining_chunks < len(page_chunks):
                page_chunks = page_chunks[:remaining_chunks]
            total_chunks = len(page_chunks)
            translated_chunks = []
            for chunk_index, chunk in enumerate(page_chunks, start=1):
                print(
                    f"Translating page {page_index}/{total_pages} "
                    f"(chunk {chunk_index}/{total_chunks})...",
                    file=sys.stderr,
                )
                translated_chunks.append(translator.translate_chunk(chunk))
                if remaining_chunks is not None:
                    remaining_chunks -= 1
            translated_pages.append("\n\n".join(translated_chunks))
            if remaining_chunks is not None and remaining_chunks <= 0:
                print("Max chunks reached. Stopping early.", file=sys.stderr)
                break
        write_pdf_pages(translated_pages, args.output)
        return

    full_text = "\n\n".join(page_texts)
    chunks = chunk_text(full_text, args.chunk_size)
    if not chunks:
        raise ValueError("No text to translate.")
    if args.max_chunks > 0:
        chunks = chunks[: args.max_chunks]

    translated_chunks = []
    total = len(chunks)
    for i, chunk in enumerate(chunks, start=1):
        print(f"Translating chunk {i}/{total}...", file=sys.stderr)
        translated_chunks.append(translator.translate_chunk(chunk))

    translated_text = "\n\n".join(translated_chunks)
    write_pdf(translated_text, args.output)


if __name__ == "__main__":
    main()
