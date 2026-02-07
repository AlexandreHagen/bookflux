from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from statistics import median

import pdfplumber
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from .output_utils import FormattingIssue, FormattingIssueReport
from .text_utils import (
    first_non_empty_index,
    last_non_empty_index,
    merge_lines,
    should_merge_lines,
    split_first_token,
)

MIN_READABLE_FONT_SIZE = 9.0
HEADING_SIZE_RATIO = 1.2
HEADING_TOLERANCE = 0.5
LINE_HEIGHT_MIN = 1.05
LINE_HEIGHT_MAX = 1.4


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


@dataclass(frozen=True)
class TypographyProfile:
    body_font_size: float
    heading_targets: list[float]


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

    lines_sorted = sorted(lines, key=lambda line: (line.top, line.x0))
    line_heights = [max(line.bottom - line.top, 1.0) for line in lines_sorted]
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
        text = "\n".join(line.text for line in block_lines if line.text)
        x0 = min(line.x0 for line in block_lines)
        x1 = max(line.x1 for line in block_lines)
        top = min(line.top for line in block_lines)
        bottom = max(line.bottom for line in block_lines)
        font_size = _median([line.size for line in block_lines], default=11.0)
        result.append(
            TextBlock(text=text, x0=x0, x1=x1, top=top, bottom=bottom, font_size=font_size)
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


def _split_word(word: str, max_width: float, font_name: str, font_size: float) -> list[str]:
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


def _wrap_paragraph(text: str, max_width: float, font_name: str, font_size: float) -> list[str]:
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


def _wrap_text(text: str, max_width: float, font_name: str, font_size: float) -> list[str]:
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
) -> tuple[float, list[str], float, bool, bool, list[str]]:
    font_size = max(base_size, min_size)
    while font_size >= min_size:
        lines = _wrap_text(text, max_width, font_name, font_size)
        for ratio in (line_height_ratio, LINE_HEIGHT_MIN):
            line_height = font_size * ratio
            if len(lines) * line_height <= max_height:
                scaled_down = font_size < base_size
                return font_size, lines, line_height, False, scaled_down, []
        font_size -= 0.5

    font_size = min_size
    lines = _wrap_text(text, max_width, font_name, font_size)
    line_height = font_size * LINE_HEIGHT_MIN
    max_lines = max(int(max_height // line_height), 1)
    truncated = len(lines) > max_lines
    remaining = []
    if truncated:
        remaining = lines[max_lines:]
        lines = lines[:max_lines]
    scaled_down = font_size < base_size
    return font_size, lines, line_height, truncated, scaled_down, remaining


def _cluster_sizes(sizes: list[float], tolerance: float) -> list[list[float]]:
    if not sizes:
        return []
    sorted_sizes = sorted(sizes)
    clusters = [[sorted_sizes[0]]]
    for size in sorted_sizes[1:]:
        if size - clusters[-1][-1] <= tolerance:
            clusters[-1].append(size)
        else:
            clusters.append([size])
    return clusters


def _infer_body_font_size(sizes: list[float], default: float) -> float:
    if not sizes:
        return default
    sorted_sizes = sorted(sizes)
    min_size = sorted_sizes[0]
    max_size = sorted_sizes[-1]
    if min_size > 0 and max_size >= min_size * HEADING_SIZE_RATIO:
        return min_size
    return _median(sorted_sizes, default=default)


def _match_heading_target(size: float, targets: list[float], tolerance: float) -> float:
    if not targets:
        return size
    closest = min(targets, key=lambda target: abs(target - size))
    if abs(closest - size) <= tolerance:
        return closest
    return size


def extract_typography_profile(
    pages: list[list[TextBlock]],
    heading_ratio: float = HEADING_SIZE_RATIO,
) -> TypographyProfile:
    sizes = [block.font_size for page in pages for block in page if block.font_size]
    body_size = _infer_body_font_size(sizes, default=11.0)
    heading_threshold = body_size * heading_ratio
    heading_sizes = [
        block.font_size for page in pages for block in page if block.font_size >= heading_threshold
    ]
    clusters = _cluster_sizes(heading_sizes, HEADING_TOLERANCE)
    targets = [max(_median(cluster, default=cluster[0]), heading_threshold) for cluster in clusters]
    return TypographyProfile(body_font_size=body_size, heading_targets=targets)


def _build_summary(issues: list[FormattingIssue]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for issue in issues:
        summary[issue.issue_type] = summary.get(issue.issue_type, 0) + 1
    return summary


def write_pdf_layout(
    pages: list[list[TextBlock]],
    page_sizes: list[tuple[float, float]],
    output_path: str,
    font_name: str = "Times-Roman",
    min_font_size: float = MIN_READABLE_FONT_SIZE,
    line_height_ratio: float = LINE_HEIGHT_MAX,
    allow_page_overflow: bool = False,
    overflow_extra: float = 0.0,
) -> FormattingIssueReport:
    c = canvas.Canvas(output_path)
    profile = extract_typography_profile(pages)
    heading_min_size = max(min_font_size, profile.body_font_size * HEADING_SIZE_RATIO)
    issues: list[FormattingIssue] = []
    overflow_margin = 72.0

    for page_index, blocks in enumerate(pages):
        width, height = page_sizes[page_index]
        c.setPageSize((width, height))
        overflow_entries: list[tuple[list[str], float, float, float]] = []
        for block_index, block in enumerate(blocks):
            if not block.text.strip():
                continue
            box_width = max(block.x1 - block.x0, 1.0)
            box_height = max(block.bottom - block.top, 1.0)
            overflow_height = box_height
            if block_index < len(blocks) - 1:
                next_block = blocks[block_index + 1]
                gap = max(next_block.top - block.bottom, 0.0)
                if gap > 1.0:
                    overflow_height = box_height + gap + max(overflow_extra, 0.0)
            base_size = _match_heading_target(
                block.font_size,
                profile.heading_targets,
                HEADING_TOLERANCE,
            )
            min_size = min_font_size
            if block.font_size >= profile.body_font_size * HEADING_SIZE_RATIO:
                base_size = max(base_size, heading_min_size)
                min_size = heading_min_size
            font_size, lines, line_height, truncated, scaled_down, remaining = _fit_text_to_box(
                block.text,
                box_width,
                box_height,
                font_name,
                base_size,
                min_size,
                line_height_ratio,
            )
            overflow_used = False
            if truncated and overflow_height > box_height:
                font_size, lines, line_height, truncated, scaled_down, remaining = _fit_text_to_box(
                    block.text,
                    box_width,
                    overflow_height,
                    font_name,
                    base_size,
                    min_size,
                    line_height_ratio,
                )
                overflow_used = True
            if truncated and allow_page_overflow and remaining:
                overflow_entries.append((remaining, font_size, line_height, block.x0))
                overflow_used = True
                truncated = False
            if overflow_used:
                issues.append(
                    FormattingIssue(
                        page_number=page_index + 1,
                        issue_type="overflow_used",
                        description="Text overflowed into available vertical gap.",
                        severity="low",
                    )
                )
            if truncated:
                issues.append(
                    FormattingIssue(
                        page_number=page_index + 1,
                        issue_type="truncation",
                        description="Text truncated to fit layout block.",
                        severity="high",
                    )
                )
            if scaled_down:
                issues.append(
                    FormattingIssue(
                        page_number=page_index + 1,
                        issue_type="font_scaled_down",
                        description="Font size reduced to fit layout block.",
                        severity="medium",
                    )
                )
            c.setFont(font_name, font_size)
            y = height - block.top - font_size
            for line in lines:
                if line:
                    c.drawString(block.x0, y, line)
                y -= line_height

        if overflow_entries:
            c.showPage()
            c.setPageSize((width, height))
            y = height - overflow_margin
            for lines, font_size, line_height, x0 in overflow_entries:
                c.setFont(font_name, font_size)
                for line in lines:
                    if y - line_height < overflow_margin:
                        issues.append(
                            FormattingIssue(
                                page_number=page_index + 1,
                                issue_type="truncation",
                                description="Text truncated after page overflow.",
                                severity="high",
                            )
                        )
                        break
                    if line:
                        c.drawString(x0, y, line)
                    y -= line_height

        if page_index < len(pages) - 1:
            c.showPage()

    c.save()
    run_id = Path(output_path).stem
    return FormattingIssueReport(run_id=run_id, issues=issues, summary=_build_summary(issues))


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
