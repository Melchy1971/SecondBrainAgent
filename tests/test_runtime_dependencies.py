from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_cryptography_is_an_installed_core_dependency() -> None:
    import cryptography

    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependencies = pyproject["project"]["dependencies"]
    runtime_requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()

    assert cryptography.__version__
    assert any(item.startswith("cryptography>=") for item in dependencies)
    assert any(item.startswith("cryptography>=") for item in runtime_requirements)
