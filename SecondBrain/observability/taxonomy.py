"""Error Taxonomy: Fehler nach Ursache klassifizieren und gruppieren."""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable

ERROR_CATEGORIES: tuple[str, ...] = (
    "configuration", "network", "provider", "storage", "parsing",
    "permission", "timeout", "validation", "resource", "unknown",
)

_TYPE_MAP: dict[str, str] = {
    "FileNotFoundError": "storage",
    "IsADirectoryError": "storage",
    "NotADirectoryError": "storage",
    "OSError": "storage",
    "IOError": "storage",
    "PermissionError": "permission",
    "TimeoutError": "timeout",
    "ConnectionError": "network",
    "ConnectionRefusedError": "network",
    "ConnectionResetError": "network",
    "BrokenPipeError": "network",
    "ValueError": "validation",
    "TypeError": "validation",
    "KeyError": "validation",
    "JSONDecodeError": "parsing",
    "UnicodeDecodeError": "parsing",
    "SyntaxError": "parsing",
    "MemoryError": "resource",
    "RecursionError": "resource",
    "ModuleNotFoundError": "configuration",
    "ImportError": "configuration",
}

_MESSAGE_MARKERS: tuple[tuple[str, str], ...] = (
    ("api key", "configuration"),
    ("api-key", "configuration"),
    ("unauthorized", "permission"),
    ("forbidden", "permission"),
    ("401", "permission"),
    ("403", "permission"),
    ("429", "provider"),
    ("rate limit", "provider"),
    ("quota", "provider"),
    ("model", "provider"),
    ("timeout", "timeout"),
    ("timed out", "timeout"),
    ("connection", "network"),
    ("dns", "network"),
    ("ssl", "network"),
    ("database", "storage"),
    ("disk", "storage"),
    ("parse", "parsing"),
    ("decode", "parsing"),
    ("ocr", "parsing"),
    ("config", "configuration"),
    ("env", "configuration"),
)


def classify_error(error: BaseException | str, error_type: str | None = None) -> str:
    """Klassifiziert eine Exception oder Fehlermeldung in eine Ursachen-Kategorie."""
    if isinstance(error, BaseException):
        type_name = type(error).__name__
        message = str(error)
    else:
        type_name = error_type or ""
        message = str(error)
    if type_name in _TYPE_MAP:
        return _TYPE_MAP[type_name]
    lowered = message.lower()
    for marker, category in _MESSAGE_MARKERS:
        if marker in lowered:
            return category
    return "unknown"


def group_by_cause(events: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Gruppiert Fehler-Events nach Kategorie (für GUI und Reports)."""
    counter: Counter[str] = Counter()
    samples: dict[str, list[dict[str, Any]]] = {}
    total = 0
    for event in events:
        category = event.get("category") or classify_error(
            str(event.get("message", "")), event.get("error_type"))
        counter[category] += 1
        total += 1
        bucket = samples.setdefault(category, [])
        if len(bucket) < 3:
            bucket.append({k: event.get(k) for k in ("ts", "event", "message", "correlation_id")})
    return {
        "schema": "secondbrain.observability.error_groups.v1",
        "total": total,
        "by_category": dict(counter.most_common()),
        "samples": samples,
    }
