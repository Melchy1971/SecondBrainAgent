from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dev_extra_installs_document_test_readers() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    requirements = pyproject["project"]["optional-dependencies"]["dev"]
    names = {
        re.split(r"[<>=!~\[]", requirement, maxsplit=1)[0].strip().lower()
        for requirement in requirements
    }

    assert {"pillow", "pymupdf", "pypdf", "python-docx"}.issubset(names)
