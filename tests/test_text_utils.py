from bookflux import text_utils


def test_split_first_token() -> None:
    assert text_utils.split_first_token("hello world") == ("hello", "world")
    assert text_utils.split_first_token("  solo") == ("solo", "")
    assert text_utils.split_first_token("") == ("", "")


def test_merge_lines_hyphenates() -> None:
    assert text_utils.merge_lines("hyphen-", "ated word") == "hyphenated word"


def test_looks_like_page_number() -> None:
    assert text_utils.looks_like_page_number("12") is True
    assert text_utils.looks_like_page_number("  1234 ") is True
    assert text_utils.looks_like_page_number("12345") is False
    assert text_utils.looks_like_page_number("Page 1") is False


def test_should_merge_lines_skips_headings() -> None:
    assert text_utils.should_merge_lines("INTRODUCTION", "Some text") is False
    assert text_utils.should_merge_lines("Some text", "CHAPTER ONE") is False


def test_should_merge_lines_allows_numbers() -> None:
    assert text_utils.should_merge_lines("123 456", "next line") is True


def test_non_empty_index_helpers() -> None:
    lines = ["", "first", "", "last", ""]
    assert text_utils.first_non_empty_index(lines) == 1
    assert text_utils.last_non_empty_index(lines) == 3
    assert text_utils.first_non_empty_index(["", " "]) is None
    assert text_utils.last_non_empty_index(["", " "]) is None
