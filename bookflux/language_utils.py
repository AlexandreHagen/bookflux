from __future__ import annotations

import logging

from langcodes import Language


def language_display_name(code: str) -> str:
    clean = (code or "").strip()
    if not clean:
        return clean
    try:
        language = Language.get(clean)
        if hasattr(language, "is_valid") and not language.is_valid():
            return clean
        name = language.display_name("en")
    except Exception as exc:
        logging.getLogger(__name__).debug(
            "Failed to resolve language code '%s'.", clean, exc_info=exc
        )
        return clean
    if not name:
        return clean
    lowered = name.lower()
    if lowered.startswith("unknown") or "unknown language" in lowered:
        return clean
    return name
