from __future__ import annotations

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


def _wrap_paragraph(
    text: str, max_width: float, font_name: str, font_size: int
) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if stringWidth(candidate, font_name, font_size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _iter_render_lines(
    text: str, max_width: float, font_name: str, font_size: int
) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            lines.append("")
            continue
        lines.extend(_wrap_paragraph(paragraph, max_width, font_name, font_size))
    return lines


def write_pdf(
    text: str,
    output_path: str,
    pagesize=letter,
    font_name: str = "Times-Roman",
    font_size: int = 11,
) -> None:
    c = canvas.Canvas(output_path, pagesize=pagesize)
    width, height = pagesize
    margin = 72
    line_height = font_size * 1.4

    c.setFont(font_name, font_size)
    y = height - margin

    for line in _iter_render_lines(
        text, width - 2 * margin, font_name, font_size
    ):
        if y - line_height < margin:
            c.showPage()
            c.setFont(font_name, font_size)
            y = height - margin

        if not line:
            y -= line_height
            continue

        c.drawString(margin, y, line)
        y -= line_height

    c.save()


def write_pdf_pages(
    pages: list[str],
    output_path: str,
    pagesize=letter,
    font_name: str = "Times-Roman",
    font_size: int = 11,
) -> None:
    c = canvas.Canvas(output_path, pagesize=pagesize)
    width, height = pagesize
    margin = 72
    line_height = font_size * 1.4

    c.setFont(font_name, font_size)
    y = height - margin

    for page_index, page_text in enumerate(pages):
        if page_index > 0:
            c.showPage()
            c.setFont(font_name, font_size)
            y = height - margin

        for line in _iter_render_lines(
            page_text, width - 2 * margin, font_name, font_size
        ):
            if y - line_height < margin:
                c.showPage()
                c.setFont(font_name, font_size)
                y = height - margin

            if not line:
                y -= line_height
                continue

            c.drawString(margin, y, line)
            y -= line_height

    c.save()
