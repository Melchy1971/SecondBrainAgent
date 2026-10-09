"""Modulpfade des nativen Workspace muessen in exakter Schreibweise existieren.

Windows ignoriert Gross-/Kleinschreibung, Linux/macOS nicht. Frueher standen die
Kandidaten als ``secondbrain/...`` im Register, der Ordner heisst aber
``SecondBrain/`` (``secondbrain`` ist nur ein Import-Shim). Unter Linux galten
dadurch alle Module als ``missing``. Dieser Test prueft die Schreibweise auch
auf Windows.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from secondbrain.native.ai_workspace.service import AIWorkspaceService

ROOT = Path(__file__).resolve().parents[1]


def _exists_with_exact_case(root: Path, relative: str) -> bool:
    current = root
    for part in relative.split("/"):
        if part not in os.listdir(current):
            return False
        current = current / part
    return True


@pytest.mark.parametrize("module_id,candidates", [(m[0], m[3]) for m in AIWorkspaceService.MODULES])
def test_module_candidate_exists_with_exact_case(module_id: str, candidates: tuple[str, ...]) -> None:
    assert any(_exists_with_exact_case(ROOT, c) for c in candidates), (
        f"{module_id}: keiner der Pfade {candidates} existiert in exakter Schreibweise"
    )
