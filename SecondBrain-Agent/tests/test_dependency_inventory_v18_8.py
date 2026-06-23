from __future__ import annotations

from pathlib import Path

from secondbrain.module_registry import ModuleRegistry
from secondbrain.release.dependency_inventory import build_dependency_inventory, render_requirements


def test_dependency_inventory_classifies_imports(tmp_path: Path) -> None:
    pkg = tmp_path / "secondbrain"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "feature.py").write_text(
        "import json\n"
        "import requests\n"
        "from secondbrain import local\n"
        "from pathlib import Path\n",
        encoding="utf-8",
    )

    report = build_dependency_inventory(tmp_path)
    payload = report.to_dict()

    assert payload["ok"] is True
    assert "json" in payload["standard_library"]
    assert "pathlib" in payload["standard_library"]
    assert "secondbrain" in payload["internal"]
    assert "requests" in payload["external"]
    assert "requests" in payload["requirements_suggestion"]


def test_dependency_inventory_marks_provider_as_optional(tmp_path: Path) -> None:
    pkg = tmp_path / "secondbrain"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "provider.py").write_text("import openai\nimport google\n", encoding="utf-8")

    payload = build_dependency_inventory(tmp_path).to_dict()

    assert "openai" in payload["optional_provider"]
    assert "google" in payload["optional_provider"]
    assert "openai" in payload["optional_requirements_suggestion"]
    assert "google-generativeai or google-api-python-client" in payload["optional_requirements_suggestion"]


def test_dependency_inventory_writes_report(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("import json\n", encoding="utf-8")

    report = build_dependency_inventory(tmp_path, write_report=True)

    assert report.ok is True
    assert (tmp_path / "release" / "dependency_inventory_latest.json").exists()


def test_render_requirements_applies_aliases() -> None:
    assert render_requirements(["yaml", "PIL"]) == ["Pillow", "PyYAML"]


def test_command_index_exposes_dependency_inventory() -> None:
    registry = ModuleRegistry()

    assert registry.command_index()["dependency-inventory"] == "core"
    assert registry.resolve_command("dependency-inventory").key == "core"
