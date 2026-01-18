from __future__ import annotations

from dataclasses import dataclass
from statistics import median
import sys
from typing import Iterable

import pdfplumber
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from .text_utils import (
    first_non_empty_index,
    last_non_empty_index,
    merge_lines,
    should_merge_lines,
    split_first_token,
)

@dataclass(frozen=True)
class TextLine:
    text: str
    x0: float
    x1: float
    top: float
    bottom: float
    size: float


@dataclass(frozen=True)
class TextBlock:
    text: str
    x0: float
    x1: float
    top: float
    bottom: float
    font_size: float


def _median(values: Iterable[float], default: float) -> float:
    values_list = [v for v in values if v]
    if not values_list:
        return default
    return float(median(values_list))


def _build_line(words: list[dict]) -> TextLine:
    words_sorted = sorted(words, key=lambda w: w["x0"])
    text = " ".join(w["text"] for w in words_sorted if w.get("text"))
    x0 = min(w["x0"] for w in words_sorted)
    x1 = max(w["x1"] for w in words_sorted)
    top = min(w["top"] for w in words_sorted)
    bottom = max(w["bottom"] for w in words_sorted)
    size = _median([w.get("size", 0) for w in words_sorted], default=11.0)
    return TextLine(text=text, x0=x0, x1=x1, top=top, bottom=bottom, size=size)


def _words_to_lines(words: list[dict], y_tolerance: float = 2.0) -> list[TextLine]:
    if not words:
        return []
    words_sorted = sorted(words, key=lambda w: (w["top"], w["x0"]))
    lines: list[TextLine] = []
    current: list[dict] = []
    current_top: float | None = None

    for word in words_sorted:
        if current_top is None:
            current = [word]
            current_top = word["top"]
            continue

        if abs(word["top"] - current_top) <= y_tolerance:
            current.append(word)
            current_top = min(current_top, word["top"])
        else:
            lines.append(_build_line(current))
            current = [word]
            current_top = word["top"]

    if current:
        lines.append(_build_line(current))

    return lines


def _split_columns(lines: list[TextLine], page_width: float) -> list[list[TextLine]]:
    if len(lines) < 6:
        return [lines]

    x0s = sorted({round(line.x0, 1) for line in lines})
    if len(x0s) < 2:
        return [lines]

    gaps = [x0s[i + 1] - x0s[i] for i in range(len(x0s) - 1)]
    max_gap = max(gaps)
    if max_gap < page_width * 0.2:
        return [lines]

    split_index = gaps.index(max_gap)
    split_x = (x0s[split_index] + x0s[split_index + 1]) / 2.0
    left = [line for line in lines if line.x0 < split_x]
    right = [line for line in lines if line.x0 >= split_x]
    if len(left) < 3 or len(right) < 3:
        return [lines]

    return [left, right]


def _lines_to_blocks(lines: list[TextLine]) -> list[TextBlock]:
    if not lines:
        return []

    lines_sorted = sorted(lines, key=lambda l: (l.top, l.x0))
    line_heights = [max(l.bottom - l.top, 1.0) for l in lines_sorted]
    gap_threshold = _median(line_heights, default=12.0) * 1.5

    blocks: list[list[TextLine]] = []
    current: list[TextLine] = [lines_sorted[0]]
    for line in lines_sorted[1:]:
        prev = current[-1]
        if line.top - prev.bottom > gap_threshold:
            blocks.append(current)
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append(current)

    result: list[TextBlock] = []
    for block_lines in blocks:
        text = "\n".join(l.text for l in block_lines if l.text)
        x0 = min(l.x0 for l in block_lines)
        x1 = max(l.x1 for l in block_lines)
        top = min(l.top for l in block_lines)
        bottom = max(l.bottom for l in block_lines)
        font_size = _median([l.size for l in block_lines], default=11.0)
        result.append(
            TextBlock(
                text=text, x0=x0, x1=x1, top=top, bottom=bottom, font_size=font_size
            )
        )

    return result


def extract_layout_blocks(
    pdf_path: str,
) -> tuple[list[tuple[float, float]], list[list[TextBlock]]]:
    page_sizes: list[tuple[float, float]] = []
    pages_blocks: list[list[TextBlock]] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_sizes.append((page.width, page.height))
            words = page.extract_words(
                x_tolerance=2,
                y_tolerance=2,
                keep_blank_chars=False,
                use_text_flow=True,
                extra_attrs=["size"],
            )
            lines = _words_to_lines(words)
            columns = _split_columns(lines, page.width)
            blocks: list[TextBlock] = []
            for column_lines in columns:
                blocks.extend(_lines_to_blocks(column_lines))
            blocks_sorted = sorted(blocks, key=lambda b: (b.top, b.x0))
            pages_blocks.append(blocks_sorted)

    return page_sizes, pages_blocks


def _split_word(
    word: str, max_width: float, font_name: str, font_size: float
) -> list[str]:
    if stringWidth(word, font_name, font_size) <= max_width:
        return [word]

    parts: list[str] = []
    current = ""
    for char in word:
        if stringWidth(current + char, font_name, font_size) <= max_width:
            current += char
        else:
            if current:
                parts.append(current)
            current = char
    if current:
        parts.append(current)
    return parts


def _wrap_paragraph(
    text: str, max_width: float, font_name: str, font_size: float
) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = ""
    for word in words:
        for piece in _split_word(word, max_width, font_name, font_size):
            candidate = f"{current} {piece}".strip() if current else piece
            if stringWidth(candidate, font_name, font_size) <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = piece
    if current:
        lines.append(current)
    return lines


def _wrap_text(
    text: str, max_width: float, font_name: str, font_size: float
) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            lines.append("")
            continue
        lines.extend(_wrap_paragraph(paragraph, max_width, font_name, font_size))
    return lines


def _fit_text_to_box(
    text: str,
    max_width: float,
    max_height: float,
    font_name: str,
    base_size: float,
    min_size: float,
    line_height_ratio: float,
) -> tuple[float, list[str], float, bool]:
    font_size = max(base_size, min_size)
    while font_size >= min_size:
        lines = _wrap_text(text, max_width, font_name, font_size)
        line_height = font_size * line_height_ratio
        if len(lines) * line_height <= max_height:
            return font_size, lines, line_height, False
        font_size -= 0.5

    font_size = min_size
    lines = _wrap_text(text, max_width, font_name, font_size)
    line_height = font_size * line_height_ratio
    max_lines = max(int(max_height // line_height), 1)
    truncated = len(lines) > max_lines
    if truncated:
        lines = lines[:max_lines]
    return font_size, lines, line_height, truncated


def write_pdf_layout(
    pages: list[list[TextBlock]],
    page_sizes: list[tuple[float, float]],
    output_path: str,
    font_name: str = "Times-Roman",
    min_font_size: float = 6.0,
    line_height_ratio: float = 1.2,
) -> None:
    c = canvas.Canvas(output_path)

    for page_index, blocks in enumerate(pages):
        width, height = page_sizes[page_index]
        c.setPageSize((width, height))
        for block in blocks:
            if not block.text.strip():
                continue
            box_width = max(block.x1 - block.x0, 1.0)
            box_height = max(block.bottom - block.top, 1.0)
            font_size, lines, line_height, truncated = _fit_text_to_box(
                block.text,
                box_width,
                box_height,
                font_name,
                block.font_size,
                min_font_size,
                line_height_ratio,
            )
            if truncated:
                print(
                    f"Warning: text truncated in block at page {page_index + 1}.",
                    file=sys.stderr,
                    flush=True,
                )
            c.setFont(font_name, font_size)
            y = height - block.top - font_size
            for line in lines:
                if line:
                    c.drawString(block.x0, y, line)
                y -= line_height

        if page_index < len(pages) - 1:
            c.showPage()

    c.save()


def merge_block_page_breaks(pages: list[list[TextBlock]]) -> list[list[TextBlock]]:
    updated = [list(page) for page in pages]

    for page_index in range(len(updated) - 1):
        current_page = updated[page_index]
        next_page = updated[page_index + 1]
        if not current_page or not next_page:
            continue

        last_block = current_page[-1]
        first_block = next_page[0]

        last_lines = last_block.text.splitlines()
        next_lines = first_block.text.splitlines()
        last_idx = last_non_empty_index(last_lines)
        next_idx = first_non_empty_index(next_lines)
        if last_idx is None or next_idx is None:
            continue

        last_line = last_lines[last_idx].rstrip()
        next_line = next_lines[next_idx].lstrip()
        if not last_line or not next_line:
            continue
        if not should_merge_lines(last_line, next_line):
            continue

        if last_line.endswith("-"):
            fragment, remainder = split_first_token(next_line)
            if not fragment:
                continue
            last_lines[last_idx] = merge_lines(last_line, fragment)
            if remainder:
                next_lines[next_idx] = remainder
            else:
                del next_lines[next_idx]
        else:
            # Only merge hyphenated page breaks to avoid reshaping page layout.
            continue

        new_last_text = "\n".join(last_lines).strip("\n")
        new_first_text = "\n".join(next_lines).strip("\n")

        if new_last_text:
            current_page[-1] = TextBlock(
                text=new_last_text,
                x0=last_block.x0,
                x1=last_block.x1,
                top=last_block.top,
                bottom=last_block.bottom,
                font_size=last_block.font_size,
            )
        else:
            current_page.pop()

        if new_first_text:
            next_page[0] = TextBlock(
                text=new_first_text,
                x0=first_block.x0,
                x1=first_block.x1,
                top=first_block.top,
                bottom=first_block.bottom,
                font_size=first_block.font_size,
            )
        else:
            next_page.pop(0)

    return updated
