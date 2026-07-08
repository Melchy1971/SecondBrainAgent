"""WCAG 2.1 contrast ratio + AA/AAA checks (accessibility)."""

from __future__ import annotations


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    c = color.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        raise ValueError(f"invalid hex color: {color!r}")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def _channel(v: int) -> float:
    s = v / 255.0
    return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4


def relative_luminance(color: str) -> float:
    r, g, b = _hex_to_rgb(color)
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(a: str, b: str) -> float:
    la, lb = relative_luminance(a), relative_luminance(b)
    lighter, darker = max(la, lb), min(la, lb)
    return (lighter + 0.05) / (darker + 0.05)


def passes_aa(fg: str, bg: str, *, large_text: bool = False) -> bool:
    return contrast_ratio(fg, bg) >= (3.0 if large_text else 4.5)


def passes_aaa(fg: str, bg: str, *, large_text: bool = False) -> bool:
    return contrast_ratio(fg, bg) >= (4.5 if large_text else 7.0)


def audit_pairs(pairs: list[tuple[str, str, str]]) -> dict:
    """pairs: (label, fg, bg). Returns per-pair ratio + AA result and overall pass."""
    results = []
    for label, fg, bg in pairs:
        ratio = round(contrast_ratio(fg, bg), 2)
        results.append({"label": label, "fg": fg, "bg": bg, "ratio": ratio, "aa": ratio >= 4.5})
    return {"results": results, "passes_aa": all(r["aa"] for r in results)}
