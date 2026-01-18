from __future__ import annotations

import argparse
import json
import sys

from .layout_utils import (
    TextBlock,
    extract_layout_blocks,
    merge_block_page_breaks,
    write_pdf_layout,
)
from .output_utils import write_pdf, write_pdf_pages
from .pdf_utils import extract_text, merge_page_texts, normalize_page_texts
from .providers import create_provider, list_providers
from .translator import TranslatorFacade, chunk_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Translate a PDF book using an AI provider (default target: French)."
    )
    parser.add_argument("--input", help="Path to input PDF.")
    parser.add_argument("--output", help="Path to output PDF.")
    parser.add_argument("--lang", default="fr", help="Target language code.")
    parser.add_argument(
        "--provider",
        default=None,
        help="AI provider name (e.g., gemini).",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Provider API key (overrides environment variable).",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Provider base URL (useful for local servers).",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Provider model name (defaults to provider's default).",
    )
    parser.add_argument(
        "--provider-config",
        default=None,
        help="Path to JSON config for provider settings.",
    )
    parser.add_argument("--chunk-size", type=int, default=4000, help="Max chars per chunk.")
    parser.add_argument("--temperature", type=float, default=None, help="Model temperature.")
    parser.add_argument(
        "--request-mode",
        choices=["chat", "completion"],
        default=None,
        help="Request mode for OpenAI-compatible providers.",
    )
    parser.add_argument("--max-retries", type=int, default=None, help="Retries per chunk.")
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help="HTTP timeout in seconds for provider requests.",
    )
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=0,
        help="Translate only the first N chunks for quick tests (0 = no limit).",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models for the selected provider and exit.",
    )
    parser.add_argument(
        "--list-providers",
        action="store_true",
        help="List available providers and exit.",
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


def _load_provider_config(path: str | None) -> dict:
    if not path:
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise ValueError(f"Provider config not found: {path}") from exc
    if not isinstance(data, dict):
        raise ValueError("Provider config must be a JSON object.")
    return data


def _get_float(config: dict, key: str, default: float) -> float:
    value = config.get(key)
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid float for '{key}' in provider config.") from exc


def _get_int(config: dict, key: str, default: int) -> int:
    value = config.get(key)
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid int for '{key}' in provider config.") from exc


def list_models(
    provider_name: str,
    api_key: str | None,
    model_name: str | None,
    base_url: str | None,
    temperature: float,
    max_retries: int,
    timeout: float,
    request_mode: str | None,
) -> None:
    create_kwargs: dict[str, object] = {
        "temperature": temperature,
        "max_retries": max_retries,
        "timeout": timeout,
    }
    if request_mode is not None:
        create_kwargs["request_mode"] = request_mode
    if api_key is not None:
        create_kwargs["api_key"] = api_key
    if base_url is not None:
        create_kwargs["base_url"] = base_url
    if model_name is not None:
        create_kwargs["model_name"] = model_name
    provider = create_provider(provider_name, **create_kwargs)
    models = provider.list_models()
    if not models:
        print("No models available for this provider.", file=sys.stderr)
        return
    for name in sorted(models):
        print(name)


def main() -> None:
    args = build_parser().parse_args()
    config = _load_provider_config(args.provider_config)

    provider_name = args.provider or config.get("provider", "gemini")
    api_key = args.api_key or config.get("api_key")
    config_model_name = config.get("model_name")
    if config_model_name is None:
        config_model_name = config.get("model")
    model_name = args.model or config_model_name
    base_url = args.base_url or config.get("base_url")
    temperature = (
        args.temperature if args.temperature is not None else _get_float(config, "temperature", 0.2)
    )
    max_retries = (
        args.max_retries if args.max_retries is not None else _get_int(config, "max_retries", 3)
    )
    request_mode = args.request_mode or config.get("request_mode")
    timeout = args.timeout if args.timeout is not None else _get_float(config, "timeout", 60.0)

    if args.list_providers:
        for name in list_providers():
            print(name)
        return
    if args.list_models:
        list_models(
            provider_name,
            api_key,
            model_name,
            base_url,
            temperature,
            max_retries,
            timeout,
            request_mode,
        )
        return
    if not args.input or not args.output:
        raise ValueError("Missing required arguments: --input and --output.")

    create_kwargs: dict[str, object] = {
        "temperature": temperature,
        "max_retries": max_retries,
        "timeout": timeout,
    }
    if request_mode is not None:
        create_kwargs["request_mode"] = request_mode
    if api_key is not None:
        create_kwargs["api_key"] = api_key
    if base_url is not None:
        create_kwargs["base_url"] = base_url
    if model_name is not None:
        create_kwargs["model_name"] = model_name
    provider = create_provider(provider_name, **create_kwargs)
    translator = TranslatorFacade(provider, target_lang=args.lang)

    if args.layout == "soft":
        if args.ocr:
            raise ValueError("Soft layout does not support OCR yet.")

        page_sizes, pages_blocks = extract_layout_blocks(args.input)
        pages_blocks = merge_block_page_breaks(pages_blocks)
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

    page_texts = extract_text(args.input, use_ocr=args.ocr, ocr_lang=args.ocr_lang)

    if args.preserve_pages:
        page_texts = normalize_page_texts(page_texts)
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

    full_text = merge_page_texts(page_texts)
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
