from bookflux.language_utils import language_display_name


def test_language_display_name_simple() -> None:
    assert language_display_name("fr") == "French"


def test_language_display_name_with_region() -> None:
    assert language_display_name("pt-BR") == "Portuguese (Brazil)"


def test_language_display_name_unknown_fallback() -> None:
    assert language_display_name("xx-123") == "xx-123"
