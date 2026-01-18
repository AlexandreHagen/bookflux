from __future__ import annotations

import logging

from langcodes import Language


def language_display_name(code: str) -> str:
    clean = (code or "").strip()
    if not clean:
        return code
    try:
        language = Language.get(clean)
        if hasattr(language, "is_valid") and not language.is_valid():
            return code
        name = language.display_name("en")
    except Exception as exc:
        logging.getLogger(__name__).debug(
            "Failed to resolve language code '%s'.", clean, exc_info=exc
        )
        return code
    if not name:
        return code
    lowered = name.lower()
    if lowered.startswith("unknown") or "unknown language" in lowered:
        return code
    return name
