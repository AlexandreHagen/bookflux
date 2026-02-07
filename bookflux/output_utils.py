from __future__ import annotations

import json
from dataclasses import dataclass

from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


@dataclass(frozen=True)
class FormattingIssue:
    page_number: int
    issue_type: str
    description: str
    severity: str


@dataclass(frozen=True)
class FormattingIssueReport:
    run_id: str
    issues: list[FormattingIssue]
    summary: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "summary": dict(self.summary),
            "issues": [
                {
                    "page_number": issue.page_number,
                    "issue_type": issue.issue_type,
                    "description": issue.description,
                    "severity": issue.severity,
                }
                for issue in self.issues
            ],
        }


def write_formatting_report(report: FormattingIssueReport, output_path: str) -> None:
    payload = report.to_dict()
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def _wrap_paragraph(text: str, max_width: float, font_name: str, font_size: int) -> list[str]:
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


def _iter_render_lines(text: str, max_width: float, font_name: str, font_size: int) -> list[str]:
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

    for line in _iter_render_lines(text, width - 2 * margin, font_name, font_size):
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

        for line in _iter_render_lines(page_text, width - 2 * margin, font_name, font_size):
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
