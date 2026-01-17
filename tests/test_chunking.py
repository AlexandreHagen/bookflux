from bookflux.translator import chunk_text


def test_chunk_text_respects_max_chars() -> None:
    text = "Paragraph " + ("a" * 120)
    chunks = chunk_text(text, max_chars=50)

    assert chunks
    assert all(len(chunk) <= 50 for chunk in chunks)


def test_chunk_text_merges_short_paragraphs() -> None:
    text = "Alpha.\n\nBeta."
    chunks = chunk_text(text, max_chars=20)

    assert chunks == ["Alpha.\n\nBeta."]
