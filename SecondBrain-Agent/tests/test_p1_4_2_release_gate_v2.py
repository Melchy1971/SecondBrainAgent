from pathlib import Path
import json

from secondbrain.release import (
    CURRENT_VERSION,
    VersionInfo,
    evaluate_release_gate,
    generate_manifest,
    validate_release_consistency,
    write_release_gate_outputs,
)


def test_version_info_normalizes_patch_version():
    assert VersionInfo.parse("P1.4.2").normalized() == "P1.4.2"
    assert CURRENT_VERSION.normalized() == "P1.4.2"


def test_manifest_v2_discovers_patch_history_and_highest_passed(tmp_path: Path):
    (tmp_path / "PATCH_P1_3_7_REPORT.md").write_text("# Ingestion Index Bridge\n\n`519 passed in 19.05s`", encoding="utf-8")
    (tmp_path / "PATCH_P1_4_1_REPORT.md").write_text("# Release Manifest\n\n`3 passed in 0.90s`", encoding="utf-8")

    manifest = generate_manifest(tmp_path, version="P1.4.2")

    assert [p.key for p in manifest.patches] == ["P1_3_7", "P1_4_1"]
    assert manifest.highest_passed == 519
    assert manifest.to_dict()["patch_count"] == 2


def test_consistency_validator_detects_version_mismatch(tmp_path: Path):
    (tmp_path / "README.md").write_text("version: P1.4.1", encoding="utf-8")
    (tmp_path / "release").mkdir()
    (tmp_path / "release" / "manifest.json").write_text(json.dumps({"version": "P1.4.2"}), encoding="utf-8")
    (tmp_path / "release" / "build.json").write_text(json.dumps({"version": "P1.4.2"}), encoding="utf-8")

    report = validate_release_consistency(tmp_path, expected_version="P1.4.2")

    assert report.status == "FAIL"
    assert any(issue.code == "VERSION_MISMATCH" and issue.path == "README.md" for issue in report.issues)


def test_release_gate_passes_with_consistent_metadata_and_enough_tests(tmp_path: Path):
    (tmp_path / "PATCH_P1_3_7_REPORT.md").write_text("# Ingestion Index Bridge\n\n`519 passed in 19.05s`", encoding="utf-8")
    (tmp_path / "README.md").write_text("version: P1.4.2", encoding="utf-8")
    (tmp_path / "release").mkdir()
    (tmp_path / "release" / "manifest.json").write_text(json.dumps({"version": "P1.4.2"}), encoding="utf-8")
    (tmp_path / "release" / "build.json").write_text(json.dumps({"version": "P1.4.2"}), encoding="utf-8")

    result = evaluate_release_gate(tmp_path, version="P1.4.2", min_tests_passed=500)

    assert result.status == "PASS"
    assert result.tests_passed == 519
    assert result.blocker_count == 0


def test_release_gate_writes_outputs(tmp_path: Path):
    (tmp_path / "PATCH_P1_3_7_REPORT.md").write_text("# Ingestion Index Bridge\n\n`519 passed in 19.05s`", encoding="utf-8")
    (tmp_path / "README.md").write_text("version: P1.4.2", encoding="utf-8")

    path = write_release_gate_outputs(tmp_path, version="P1.4.2", min_tests_passed=500)

    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["version"] == "P1.4.2"
    assert data["status"] in {"PASS", "CONDITIONAL_PASS"}
    assert (tmp_path / "release" / "build.json").exists()
    assert (tmp_path / "release" / "manifest.json").exists()
