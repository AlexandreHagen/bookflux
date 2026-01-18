from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request


ERROR_BODY_LIMIT = 1000


def _truncate_error_body(body: str, limit: int = ERROR_BODY_LIMIT) -> str:
    clean = body.strip()
    if len(clean) <= limit:
        return clean
    return f"{clean[:limit]}... [truncated]"


def get_json(
    url: str, headers: dict[str, str] | None = None, timeout: float = 30
) -> dict:
    request = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8") if exc.fp else ""
        raise RuntimeError(f"HTTP {exc.code}: {_truncate_error_body(body)}") from exc
    except socket.timeout as exc:
        raise RuntimeError(f"Request to {url} timed out after {timeout}s.") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to connect to {url}.") from exc
    return json.loads(payload or "{}")


def post_json(
    url: str,
    payload: dict,
    headers: dict[str, str] | None = None,
    timeout: float = 60,
) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8") if exc.fp else ""
        raise RuntimeError(
            f"HTTP {exc.code}: {_truncate_error_body(error_body)}"
        ) from exc
    except socket.timeout as exc:
        raise RuntimeError(f"Request to {url} timed out after {timeout}s.") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Failed to connect to {url}.") from exc
    return json.loads(body or "{}")
