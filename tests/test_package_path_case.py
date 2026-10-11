"""Waechter gegen falsch geschriebene Paketpfade.

Der Paketordner heisst ``SecondBrain/``; ``secondbrain`` ist nur ein Import-Shim.
Windows ignoriert die Schreibweise, Linux/macOS nicht. Dateisystempruefungen
muessen daher ``secondbrain.path.package_dir()`` bzw. ``PACKAGE_DIRNAME`` nutzen.
"""
from __future__ import annotations

import ast
import os
from pathlib import Path

from secondbrain.path import PACKAGE_DIRNAME, package_dir

ROOT = Path(__file__).resolve().parents[1]


def _is_segment_join(node: ast.AST) -> bool:
    return (isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
            and isinstance(node.right, ast.Constant) and isinstance(node.right.value, str))


def _lowercase_package_joins(source: str) -> list[int]:
    """Zeilen mit ``<root> / "secondbrain"`` oder ``<root>.joinpath("secondbrain", ...)``.

    Nur direkt an eine Wurzel gehaengt zaehlt; ``root / ".config" / "secondbrain"``
    ist ein Konfigurationsordner und kein Paketpfad.
    """
    hits: list[int] = []
    for node in ast.walk(ast.parse(source)):
        if (_is_segment_join(node) and node.right.value == "secondbrain"
                and not _is_segment_join(node.left)):
            hits.append(node.lineno)
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "joinpath" and node.args
                and isinstance(node.args[0], ast.Constant) and node.args[0].value == "secondbrain"):
            hits.append(node.lineno)
    return sorted(hits)


def test_package_dir_exists_with_exact_case() -> None:
    assert PACKAGE_DIRNAME in os.listdir(ROOT)
    assert package_dir(ROOT).is_dir()


def test_production_code_has_no_lowercase_package_paths() -> None:
    offenders = [
        f"{path.relative_to(ROOT).as_posix()}:{line}"
        for path in sorted(package_dir(ROOT).rglob("*.py"))
        for line in _lowercase_package_joins(path.read_text(encoding="utf-8"))
    ]
    assert not offenders, "Paketpfade ueber package_dir() bilden: " + ", ".join(offenders)


def test_guard_detects_both_patterns() -> None:
    sample = (
        'a = root / "secondbrain" / "native"\n'
        'b = root.joinpath("secondbrain", "x")\n'
        'c = root / "SecondBrain"\n'
        'd = home / ".config" / "secondbrain"\n'
    )
    assert _lowercase_package_joins(sample) == [1, 2]
