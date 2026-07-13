from pathlib import Path
import json

from secondbrain.deployment.packaging import (
    PackagingRules,
    build_package_manifest,
    collect_package_files,
    write_package_manifest,
)


def _minimal_project(tmp_path: Path) -> Path:
    (tmp_path / "secondbrain").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "secondbrain" / "core.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "tests" / "test_core.py").write_text("def test_ok(): assert True\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("version: P1.4.3\n", encoding="utf-8")
    return tmp_path


def test_collect_package_files_excludes_runtime_artifacts(tmp_path):
    root = _minimal_project(tmp_path)
    (root / "debug.log").write_text("secret", encoding="utf-8")
    (root / "data.sqlite").write_text("db", encoding="utf-8")
    (root / "__pycache__").mkdir()
    (root / "__pycache__" / "core.pyc").write_bytes(b"bad")

    files, excluded = collect_package_files(root)
    paths = {item.path for item in files}

    assert "README.md" in paths
    assert "secondbrain/core.py" in paths
    assert "debug.log" not in paths
    assert "data.sqlite" not in paths
    assert excluded >= 3


def test_build_package_manifest_passes_for_minimal_project(tmp_path):
    root = _minimal_project(tmp_path)

    manifest = build_package_manifest(root, version="P1.4.3")

    assert manifest.status == "PASS"
    assert manifest.file_count == 3
    assert manifest.total_size_bytes > 0
    assert all(len(item.sha256) == 64 for item in manifest.files)


def test_build_package_manifest_fails_when_required_file_missing(tmp_path):
    (tmp_path / "secondbrain").mkdir()
    (tmp_path / "tests").mkdir()

    manifest = build_package_manifest(tmp_path, version="P1.4.3")

    assert manifest.status == "FAIL"
    assert any("missing required file: README.md" in issue for issue in manifest.issues)


def test_write_package_manifest_creates_json_output(tmp_path):
    root = _minimal_project(tmp_path)

    manifest = write_package_manifest(root, version="P1.4.3")
    payload = json.loads((root / "release" / "package_manifest.json").read_text(encoding="utf-8"))

    assert manifest.status == "PASS"
    assert payload["version"] == "P1.4.3"
    assert payload["status"] == "PASS"
    assert payload["file_count"] == 3


def test_custom_packaging_rules_can_require_additional_files(tmp_path):
    root = _minimal_project(tmp_path)
    rules = PackagingRules(required_files=("README.md", "pyproject.toml"))

    manifest = build_package_manifest(root, version="P1.4.3", rules=rules)

    assert manifest.status == "FAIL"
    assert any("pyproject.toml" in issue for issue in manifest.issues)
