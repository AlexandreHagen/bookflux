from __future__ import annotations

from typing import List

import pdfplumber

from .text_utils import (
    looks_like_page_number,
    merge_lines,
    should_merge_lines,
    split_first_token,
)

def extract_text(pdf_path: str, use_ocr: bool = False, ocr_lang: str = "eng") -> List[str]:
    if use_ocr:
        from .ocr_utils import ocr_pdf

        return ocr_pdf(pdf_path, ocr_lang=ocr_lang)

    page_texts: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_texts.append(page.extract_text() or "")

    if not any(text.strip() for text in page_texts):
        raise ValueError("No text extracted from PDF. Try --ocr for scanned PDFs.")

    return page_texts


def merge_page_texts(page_texts: List[str]) -> str:
    lines: list[str] = []
    for text in page_texts:
        lines.extend(text.replace("\r\n", "\n").split("\n"))

    if not lines:
        return ""

    merged: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            merged.append("")
            i += 1
            continue

        current = line
        while i + 1 < len(lines):
            if not lines[i + 1].strip():
                break
            next_line = lines[i + 1].lstrip()
            if looks_like_page_number(current):
                break
            if not should_merge_lines(current, next_line):
                break
            current = merge_lines(current, next_line)
            i += 1
        merged.append(current)
        i += 1

    merged_text = "\n".join(merged).strip("\n")
    return merged_text


def normalize_page_texts(page_texts: List[str]) -> List[str]:
    pages = [_merge_lines_in_text(text) for text in page_texts]
    lines_by_page = [page.split("\n") for page in pages]

    for index in range(len(lines_by_page) - 1):
        last_idx = _last_non_empty_index(lines_by_page[index])
        next_idx = _first_non_empty_index(lines_by_page[index + 1])
        if last_idx is None or next_idx is None:
            continue
        if last_idx < len(lines_by_page[index]) - 1:
            continue
        if next_idx > 0:
            continue

        last_line = lines_by_page[index][last_idx].rstrip()
        next_line = lines_by_page[index + 1][next_idx].lstrip()
        if not last_line or not next_line:
            continue
        if looks_like_page_number(last_line):
            continue
        if not should_merge_lines(last_line, next_line):
            continue

        if last_line.endswith("-"):
            fragment, remainder = split_first_token(next_line)
            if not fragment:
                continue
            lines_by_page[index][last_idx] = merge_lines(last_line, fragment)
            if remainder:
                lines_by_page[index + 1][next_idx] = remainder
            else:
                del lines_by_page[index + 1][next_idx]
        else:
            lines_by_page[index][last_idx] = merge_lines(last_line, next_line)
            del lines_by_page[index + 1][next_idx]

    return [("\n".join(lines)).strip("\n") for lines in lines_by_page]


def _merge_lines_in_text(text: str) -> str:
    lines = text.replace("\r\n", "\n").split("\n")
    merged: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            merged.append("")
            i += 1
            continue

        current = line
        while i + 1 < len(lines):
            if not lines[i + 1].strip():
                break
            next_line = lines[i + 1].lstrip()
            if looks_like_page_number(current):
                break
            if not should_merge_lines(current, next_line):
                break
            current = merge_lines(current, next_line)
            i += 1
        merged.append(current)
        i += 1
    return "\n".join(merged).strip("\n")


def _first_non_empty_index(lines: List[str]) -> int | None:
    for idx, line in enumerate(lines):
        if line.strip():
            return idx
    return None


def _last_non_empty_index(lines: List[str]) -> int | None:
    for idx in range(len(lines) - 1, -1, -1):
        if lines[idx].strip():
            return idx
    return None
