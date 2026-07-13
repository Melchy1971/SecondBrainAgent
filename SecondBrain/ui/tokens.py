"""Design tokens: spacing/typography/radii + light & dark palettes with semantic roles.

Colors chosen so foreground/background pairs meet WCAG AA (verified in tests).
"""

from __future__ import annotations

# 4px spacing scale
SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "2xl": 32, "3xl": 48}
RADII = {"sm": 4, "md": 8, "lg": 12, "pill": 999}
FONT_SIZES = {"caption": 11, "body": 13, "subtitle": 15, "title": 20, "display": 28}
FONT_FAMILY = "Segoe UI"

SEMANTIC_ROLES = (
    "bg", "surface", "surface_alt", "fg", "fg_muted", "border",
    "primary", "on_primary", "success", "warning", "error", "info", "focus",
)

DARK = {
    "bg": "#0F172A", "surface": "#111827", "surface_alt": "#1E293B",
    "fg": "#E5E7EB", "fg_muted": "#94A3B8", "border": "#334155",
    "primary": "#22D3EE", "on_primary": "#04222A",
    "success": "#34D399", "warning": "#FBBF24", "error": "#F87171",
    "info": "#38BDF8", "focus": "#22D3EE",
}

LIGHT = {
    "bg": "#FFFFFF", "surface": "#F8FAFC", "surface_alt": "#EEF2F7",
    "fg": "#0F172A", "fg_muted": "#475569", "border": "#CBD5E1",
    "primary": "#0E7490", "on_primary": "#FFFFFF",
    "success": "#047857", "warning": "#B45309", "error": "#B91C1C",
    "info": "#0369A1", "focus": "#0E7490",
}

PALETTES = {"dark": DARK, "light": LIGHT}


def palette(name: str) -> dict:
    if name not in PALETTES:
        raise ValueError(f"unknown palette: {name}")
    return dict(PALETTES[name])


def missing_roles(p: dict) -> list[str]:
    return [r for r in SEMANTIC_ROLES if r not in p]
