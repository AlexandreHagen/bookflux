from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from bookflux.pdf_utils import extract_text, merge_page_texts, normalize_page_texts


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


def test_merge_page_texts_hyphenation() -> None:
    pages = [
        "This is a hyphen-",
        "ated word at the end of the page.",
    ]

    merged = merge_page_texts(pages)

    assert "hyphenated word at the end of the page." in merged


def test_merge_page_texts_sentence_end() -> None:
    pages = [
        "This is a full sentence.",
        "New paragraph starts here.",
    ]

    merged = merge_page_texts(pages)

    assert "full sentence.\nNew paragraph" in merged


def test_normalize_page_texts_merges_across_pages() -> None:
    pages = [
        "I can",
        "only retail the truth.",
    ]

    normalized = normalize_page_texts(pages)

    assert normalized[0].endswith("I can only retail the truth.")
    assert "only retail the truth." not in (normalized[1] or "")


def test_normalize_page_texts_hyphenation_keeps_remainder() -> None:
    pages = [
        "This is a hyphen-",
        "ated word.",
    ]

    normalized = normalize_page_texts(pages)

    assert normalized[0].endswith("hyphenated")
    assert normalized[1].startswith("word.")


def test_merge_page_texts_skips_page_numbers() -> None:
    pages = [
        "Chapter 3",
        "12\nNext line.",
    ]

    merged = merge_page_texts(pages)

    assert "Chapter 3\n12\nNext line." in merged


def test_normalize_page_texts_skips_page_number_breaks() -> None:
    pages = [
        "I can",
        "12\nonly retail.",
    ]

    normalized = normalize_page_texts(pages)

    assert normalized[0].endswith("I can")
    assert normalized[1].startswith("12")
