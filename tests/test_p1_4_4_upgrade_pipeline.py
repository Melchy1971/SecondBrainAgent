from pathlib import Path
import json

from secondbrain.deployment.upgrade import (
    build_upgrade_plan,
    create_backup_plan,
    create_migration_plan,
    create_rollback_plan,
    run_preflight,
    validate_upgrade_plan,
    write_upgrade_plan,
)


def _minimal_project(tmp_path: Path) -> Path:
    (tmp_path / "secondbrain").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "README.md").write_text("version: P1.4.3\n", encoding="utf-8")
    (tmp_path / "pytest.ini").write_text("[pytest]\ntestpaths=tests\n", encoding="utf-8")
    return tmp_path


def test_preflight_passes_for_minimal_project(tmp_path):
    root = _minimal_project(tmp_path)

    report = run_preflight(root)

    assert report.status == "PASS"
    assert report.passed is True
    assert all(check.status == "PASS" for check in report.checks)


def test_preflight_fails_when_required_paths_missing(tmp_path):
    tmp_path.mkdir(exist_ok=True)

    report = run_preflight(tmp_path)

    assert report.status == "FAIL"
    assert any(check.name == "required:README.md" and check.status == "FAIL" for check in report.checks)


def test_backup_plan_hashes_existing_files_and_marks_optional_missing(tmp_path):
    root = _minimal_project(tmp_path)

    plan = create_backup_plan(root, backup_id="backup-test")

    readme = next(item for item in plan.items if item.source == "README.md")
    pyproject = next(item for item in plan.items if item.source == "pyproject.toml")
    assert plan.status == "READY"
    assert readme.sha256 is not None and len(readme.sha256) == 64
    assert readme.size_bytes > 0
    assert pyproject.required is False
    assert pyproject.sha256 is None


def test_migration_plan_contains_required_upgrade_steps():
    plan = create_migration_plan("P1.4.3", "P1.4.4")

    ids = [step.id for step in plan.steps]
    assert ids[:2] == ["preflight", "backup"]
    assert "apply_delta" in ids
    assert "run_tests" in ids
    assert all(step.status == "PENDING" for step in plan.steps)


def test_build_upgrade_plan_ready_with_rollback_metadata(tmp_path):
    root = _minimal_project(tmp_path)

    plan = build_upgrade_plan(root, from_version="P1.4.3", to_version="P1.4.4")
    status, issues = validate_upgrade_plan(plan)

    assert plan.status == "READY"
    assert plan.rollback.status == "READY"
    assert any("README.md" in step for step in plan.rollback.steps)
    assert status == "PASS"
    assert issues == ()


def test_validate_upgrade_plan_rejects_same_version(tmp_path):
    root = _minimal_project(tmp_path)

    plan = build_upgrade_plan(root, from_version="P1.4.4", to_version="P1.4.4")
    status, issues = validate_upgrade_plan(plan)

    assert status == "FAIL"
    assert "from_version and to_version must differ" in issues


def test_write_upgrade_plan_creates_release_json(tmp_path):
    root = _minimal_project(tmp_path)

    plan = write_upgrade_plan(root, from_version="P1.4.3", to_version="P1.4.4")
    payload = json.loads((root / "release" / "upgrade_plan.json").read_text(encoding="utf-8"))

    assert plan.status == "READY"
    assert payload["from_version"] == "P1.4.3"
    assert payload["to_version"] == "P1.4.4"
    assert payload["status"] == "READY"
