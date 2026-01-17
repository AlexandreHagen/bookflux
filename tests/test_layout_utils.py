from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from bookflux.layout_utils import extract_layout_blocks, write_pdf_layout


def _make_pdf(path: str, lines: list[str]) -> None:
    c = canvas.Canvas(path, pagesize=letter)
    _, height = letter
    y = height - 72
    for line in lines:
        c.drawString(72, y, line)
        y -= 14
    c.save()


def test_extract_layout_blocks(tmp_path) -> None:
    pdf_path = tmp_path / "layout.pdf"
    lines = ["Title", "Some content here", "Another line"]
    _make_pdf(str(pdf_path), lines)

    page_sizes, pages_blocks = extract_layout_blocks(str(pdf_path))

    assert len(page_sizes) == 1
    assert len(pages_blocks) == 1
    blocks = pages_blocks[0]
    assert blocks

    combined = "\n".join(block.text for block in blocks)
    for line in lines:
        assert line in combined


def test_write_pdf_layout(tmp_path) -> None:
    pdf_path = tmp_path / "layout.pdf"
    output_path = tmp_path / "out.pdf"
    lines = ["Title", "Some content here", "Another line"]
    _make_pdf(str(pdf_path), lines)

    page_sizes, pages_blocks = extract_layout_blocks(str(pdf_path))
    write_pdf_layout(pages_blocks, page_sizes, str(output_path))

    assert output_path.exists()
    assert output_path.stat().st_size > 0
