from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from bookflux.pdf_utils import extract_text


def _make_pdf(path: str, lines: list[str]) -> None:
    c = canvas.Canvas(path, pagesize=letter)
    _, height = letter
    y = height - 72
    for line in lines:
        c.drawString(72, y, line)
        y -= 14
    c.save()


def test_extract_text_reads_pdf(tmp_path) -> None:
    pdf_path = tmp_path / "sample.pdf"
    lines = ["Hello world", "Second line"]
    _make_pdf(str(pdf_path), lines)

    pages = extract_text(str(pdf_path))

    assert len(pages) == 1
    page_text = pages[0]
    for line in lines:
        assert line in page_text
