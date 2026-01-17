from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from bookflux.layout_utils import (
    TextBlock,
    extract_layout_blocks,
    merge_block_page_breaks,
    write_pdf_layout,
)


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


def test_merge_block_page_breaks() -> None:
    block1 = TextBlock(
        text="hyphen-",
        x0=0,
        x1=100,
        top=0,
        bottom=10,
        font_size=11,
    )
    block2 = TextBlock(
        text="ated word.",
        x0=0,
        x1=100,
        top=0,
        bottom=10,
        font_size=11,
    )

    merged = merge_block_page_breaks([[block1], [block2]])
    assert merged[0][0].text.endswith("hyphenated")
    assert merged[1][0].text.startswith("word.")


def test_merge_block_page_breaks_skips_page_number() -> None:
    block1 = TextBlock(
        text="hyphen-",
        x0=0,
        x1=100,
        top=0,
        bottom=10,
        font_size=11,
    )
    block2 = TextBlock(
        text="12",
        x0=0,
        x1=100,
        top=0,
        bottom=10,
        font_size=11,
    )

    merged = merge_block_page_breaks([[block1], [block2]])
    assert merged[0][0].text == "hyphen-"
    assert merged[1][0].text == "12"
