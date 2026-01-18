from __future__ import annotations


def should_merge_lines(last_line: str, next_line: str) -> bool:
    if looks_like_page_number(last_line) or looks_like_page_number(next_line):
        return False

    if _looks_like_heading(last_line) or _looks_like_heading(next_line):
        return False

    if last_line.endswith("-"):
        return True

    if _starts_with_lowercase(next_line):
        return True

    return not _ends_sentence(last_line)


def merge_lines(last_line: str, next_line: str) -> str:
    if last_line.endswith("-"):
        return last_line[:-1] + next_line.lstrip()
    return f"{last_line} {next_line}"


def looks_like_page_number(line: str) -> bool:
    clean = line.strip()
    if not clean:
        return False
    trimmed = clean.strip(" -")
    return trimmed.isdigit() and len(trimmed) <= 4


def _ends_sentence(line: str) -> bool:
    clean = line.strip()
    if not clean:
        return False
    if clean[-1] in ".!?":
        return True
    return len(clean) >= 2 and clean[-1] in "\"')]" and clean[-2] in ".!?"


def _starts_with_lowercase(line: str) -> bool:
    for ch in line:
        if ch.isalpha():
            return ch.islower()
    return False


def _looks_like_heading(line: str) -> bool:
    letters = [ch for ch in line if ch.isalpha()]
    if len(letters) < 4:
        return False
    if not all(ch.isupper() for ch in letters):
        return False
    words = line.split()
    return len(words) <= 8


def split_first_token(line: str) -> tuple[str, str]:
    clean = line.lstrip()
    if not clean:
        return "", ""
    parts = clean.split(None, 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def first_non_empty_index(lines: list[str]) -> int | None:
    for idx, line in enumerate(lines):
        if line.strip():
            return idx
    return None


def last_non_empty_index(lines: list[str]) -> int | None:
    for idx in range(len(lines) - 1, -1, -1):
        if lines[idx].strip():
            return idx
    return None
