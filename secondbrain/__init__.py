"""Lowercase import compatibility for the historical ``SecondBrain`` source tree.

The repository keeps its implementation in ``SecondBrain/`` while all runtime code
imports ``secondbrain``.  Editable and wheel installs must therefore expose the
implementation directory as part of this package's search path.
"""
from __future__ import annotations

from importlib.util import find_spec
from pathlib import Path

_here = Path(__file__).resolve().parent
__path__ = [str(_here)]

_legacy_spec = find_spec("SecondBrain")
if _legacy_spec is not None and _legacy_spec.submodule_search_locations:
    for _location in _legacy_spec.submodule_search_locations:
        if _location not in __path__:
            __path__.append(_location)

from secondbrain.version import __build__, __version__, get_build_number, get_version, version_info

__all__ = ["__version__", "__build__", "get_version", "get_build_number", "version_info"]
