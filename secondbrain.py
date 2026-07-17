"""Portable lowercase import shim for the historical ``SecondBrain`` package."""
from __future__ import annotations

from pathlib import Path

__path__ = [str(Path(__file__).resolve().parent / "SecondBrain")]

from secondbrain.version import __build__, __version__, get_build_number, get_version, version_info

__all__ = ["__version__", "__build__", "get_version", "get_build_number", "version_info"]
