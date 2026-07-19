from __future__ import annotations

import json
import subprocess
from pathlib import Path

from secondbrain.module_registry import ModuleRegistry
from secondbrain.release.repo_doctor import REQUIRED_PATHS, _run_command, run_repo_doctor


def test_failed_health_command_reports_affected_modules(monkeypatch, tmp_path: Path) -> None:
    payload = {
        "status": "degraded",
        "runtime_health": {
            "modules": [
                {
                    "key": "desktop",
                    "status": "error",
                    "critical": True,
                    "error": "display unavailable",
                },
                {"key": "core", "status": "ok", "critical": True, "result": {"healthy": True}},
            ]
        },
    }

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 1, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    check = _run_command(tmp_path, ("health",), 10)

    assert check.details["health_status"] == "degraded"
    assert check.details["failed_modules"] == [
        {
            "section": "runtime_health",
            "key": "desktop",
            "status": "error",
            "critical": True,
            "error": "display unavailable",
            "result": None,
        }
    ]


PYPROJECT = """[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "secondbrain-agent"
version = "18.11.0"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0.0"]
pdf = ["PyMuPDF>=1.24.0", "pypdf>=5.0.0"]
connectors = ["requests>=2.31.0", "python-dotenv>=1.0.0"]
openai = ["openai>=1.40.0"]
all = ["pytest>=8.0.0", "PyMuPDF>=1.24.0", "pypdf>=5.0.0", "requests>=2.31.0", "python-dotenv>=1.0.0", "openai>=1.40.0"]

[project.scripts]
secondbrain = "launcher:main"

[tool.setuptools.packages.find]
include = ["SecondBrain", "SecondBrain.*"]
"""

def _write_minimal_project(root: Path) -> None:
    (root / "SecondBrain").mkdir(parents=True)
    (root / "SecondBrain" / "release").mkdir(parents=True)
    (root / "docs").mkdir(parents=True)
    (root / "docs" / "releases").mkdir(parents=True)
    (root / "SecondBrain" / "module_registry.py").write_text("", encoding="utf-8")
    (root / "SecondBrain" / "launcher_runtime_v126.py").write_text("", encoding="utf-8")
    (root / "SecondBrain" / "p0_runtime.py").write_text("", encoding="utf-8")
    (root / "SecondBrain" / "p1_rag_runtime.py").write_text("", encoding="utf-8")
    (root / "SecondBrain" / "release" / "dependency_inventory.py").write_text("", encoding="utf-8")
    (root / "docs" / "RELEASE_WORKFLOW_v18_9.md").write_text("# Release Workflow\n", encoding="utf-8")
    (root / "docs" / "releases" / "v18_11_P0_REPRODUCIBILITY.md").write_text("# P0 Reproducibility\n", encoding="utf-8")
    (root / "launcher.py").write_text("print('ok')\n", encoding="utf-8")
    (root / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    (root / "requirements.txt").write_text("# core runtime uses stdlib\n", encoding="utf-8")
    (root / "requirements-dev.txt").write_text("-r requirements.txt\npytest>=8.0.0\n", encoding="utf-8")
    (root / "requirements-runtime.txt").write_text("# Optional feature dependencies are declared in pyproject.toml extras.\n", encoding="utf-8")
    (root / "pytest.ini").write_text("[pytest]\ntestpaths = tests\npythonpath = .\n", encoding="utf-8")
    (root / "README.md").write_text("# SecondBrain-Agent v18.x\n\npython launcher.py health\n\npip install -e \".[dev]\"\n\nRelease docs: docs/releases\n", encoding="utf-8")

    repo = root.parent
    workflow_dir = repo / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    (workflow_dir / "secondbrain-ci.yml").write_text(
        "pip install -e \".[dev]\"\n"
        "python launcher.py version-sync\n"
        "git diff --exit-code README.md docs/09_MASTERPLAN_STATUS.json\n"
        "python launcher.py repo-doctor --execute-runtime-checks --write-report\n"
        "python launcher.py dependency-inventory --write-report\n"
        "pytest -q -m \"(release or connector) and not live and not gui\" \\\n"
        "pytest -q -m \"integration and not live and not gui\" tests/integration tests/connectors_runtime tests/storage tests/vision tests/voice\n"
        "python launcher.py rc-gate --write-report\n",
        encoding="utf-8",
    )


def test_required_runtime_paths_match_packaged_module_case() -> None:
    runtime_paths = [path for path in REQUIRED_PATHS if path.lower().startswith("secondbrain/")]

    assert runtime_paths
    assert all(path.startswith("SecondBrain/") for path in runtime_paths)


def test_repo_doctor_accepts_minimal_valid_project(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)

    report = run_repo_doctor(tmp_path)
    payload = report.to_dict()

    assert payload["ok"] is True
    assert payload["summary"]["error"] == 0
    assert any(check["key"] == "pyproject.toml:[project]" for check in payload["checks"])
    assert any(check["key"] == "requirements-runtime.txt:policy" and check["status"] == "ok" for check in payload["checks"])


def test_repo_doctor_blocks_missing_required_path(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    (tmp_path / "launcher.py").unlink()

    report = run_repo_doctor(tmp_path)
    payload = report.to_dict()

    assert payload["ok"] is False
    assert any(check["key"] == "launcher.py" and check["status"] == "error" for check in payload["checks"])


def test_repo_doctor_blocks_deleted_changelog_reference(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    (tmp_path / "README.md").write_text("# SecondBrain-Agent v18.x\n\npython launcher.py health\n\nCHANGELOG_*.md\n", encoding="utf-8")

    payload = run_repo_doctor(tmp_path).to_dict()

    assert payload["ok"] is False
    assert any(check["key"] == "README.md:deleted-changelog-reference" and check["status"] == "error" for check in payload["checks"])


def test_repo_doctor_blocks_forbidden_root_artifacts(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    (tmp_path / "PATCH_OLD_REPORT.md").write_text("obsolete", encoding="utf-8")

    payload = run_repo_doctor(tmp_path).to_dict()

    assert payload["ok"] is False
    assert any(check["key"] == "repo:forbidden-artifacts" and check["status"] == "error" for check in payload["checks"])



def test_repo_doctor_blocks_local_config_paths(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "settings.yaml").write_text("vault_path: H:\\Local\\Vault\n", encoding="utf-8")

    payload = run_repo_doctor(tmp_path).to_dict()

    assert payload["ok"] is False
    assert any(check["key"] == "repo:local-path-dependencies" and check["status"] == "error" for check in payload["checks"])

def test_repo_doctor_reports_pycache_outside_virtualenv_as_diagnostic(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    cache = tmp_path / "secondbrain" / "__pycache__"
    cache.mkdir()
    (cache / "module.cpython-313.pyc").write_bytes(b"cache")

    payload = run_repo_doctor(tmp_path).to_dict()

    assert payload["ok"] is True
    assert any(check["key"] == "repo:cache-artifacts" and check["status"] == "warning" for check in payload["checks"])


def test_repo_doctor_ignores_virtualenv_cache_artifacts(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    cache = tmp_path / ".venv" / "Lib" / "site-packages" / "pkg" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "module.cpython-313.pyc").write_bytes(b"cache")

    payload = run_repo_doctor(tmp_path).to_dict()

    assert payload["ok"] is True
    assert any(check["key"] == "repo:forbidden-artifacts" and check["status"] == "ok" for check in payload["checks"])


def test_repo_doctor_ignores_pytest_temp_and_gitignored_runtime(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)
    (tmp_path / ".gitignore").write_text("runtime/\n", encoding="utf-8")
    (tmp_path / "runtime").mkdir()
    (tmp_path / "runtime" / "local.log").write_text("runtime", encoding="utf-8")
    cache = tmp_path / ".pytest_tmp_previous" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "module.pyc").write_bytes(b"cache")

    payload = run_repo_doctor(tmp_path).to_dict()

    assert payload["ok"] is True
    assert any(check["key"] == "repo:forbidden-artifacts" and check["status"] == "ok" for check in payload["checks"])


def test_repo_doctor_writes_report(tmp_path: Path) -> None:
    _write_minimal_project(tmp_path)

    report = run_repo_doctor(tmp_path, write_report=True)

    assert report.ok is True
    assert (tmp_path / "release" / "repo_doctor_latest.json").exists()


def test_command_index_exposes_repo_doctor() -> None:
    registry = ModuleRegistry()

    assert registry.command_index()["repo-doctor"] == "core"
    assert registry.command_index()["rc-gate"] == "core"
    assert registry.resolve_command("repo-doctor").key == "core"
    assert registry.resolve_command("rc-gate").key == "core"
