"""Responsive layout: window width -> layout mode + sidebar/columns."""

from __future__ import annotations

from dataclasses import dataclass

# breakpoint lower bounds (px)
COMPACT = 0
REGULAR = 900
WIDE = 1400


@dataclass(frozen=True)
class Layout:
    mode: str          # compact | regular | wide
    sidebar: str       # collapsed | expanded
    columns: int
    content_max_width: int | None


def layout_for(width: int) -> Layout:
    if width < REGULAR:
        return Layout("compact", "collapsed", 1, None)
    if width < WIDE:
        return Layout("regular", "expanded", 2, 1200)
    return Layout("wide", "expanded", 3, 1600)
