from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from bookflux.layout_utils import (
    HEADING_SIZE_RATIO,
    MIN_READABLE_FONT_SIZE,
    TextBlock,
    _fit_text_to_box,
    extract_layout_blocks,
    extract_typography_profile,
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
    report = write_pdf_layout(pages_blocks, page_sizes, str(output_path))

    assert output_path.exists()
    assert output_path.stat().st_size > 0
    assert set(report.summary.keys()).issubset({"truncation", "font_scaled_down", "overflow_used"})


def test_heading_hierarchy_profile() -> None:
    pages = [
        [
            TextBlock(text="Heading", x0=0, x1=100, top=0, bottom=10, font_size=14.0),
            TextBlock(text="Body", x0=0, x1=100, top=20, bottom=30, font_size=10.0),
        ]
    ]
    profile = extract_typography_profile(pages)
    assert profile.body_font_size == 10.0
    assert profile.heading_targets
    target_size = profile.heading_targets[0]
    assert target_size >= profile.body_font_size * HEADING_SIZE_RATIO


def test_heading_consistency_targets_single_level() -> None:
    pages = [
        [
            TextBlock(text="Heading A", x0=0, x1=100, top=0, bottom=10, font_size=14.1),
            TextBlock(text="Heading B", x0=0, x1=100, top=20, bottom=30, font_size=14.3),
            TextBlock(text="Body", x0=0, x1=100, top=40, bottom=50, font_size=10.0),
        ]
    ]
    profile = extract_typography_profile(pages)
    assert len(profile.heading_targets) == 1
    target_size = profile.heading_targets[0]
    assert abs(target_size - 14.2) < 0.3


def test_fit_text_respects_min_font_size() -> None:
    text = "This is a long sentence that should wrap." * 5
    font_size, _, _, _, _, _ = _fit_text_to_box(
        text=text,
        max_width=50,
        max_height=40,
        font_name="Times-Roman",
        base_size=12.0,
        min_size=MIN_READABLE_FONT_SIZE,
        line_height_ratio=1.2,
    )
    assert font_size >= MIN_READABLE_FONT_SIZE


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
