from __future__ import annotations

from pathlib import Path


EXPECTED_COMMANDS = (
    'pip install -e ".[dev]"',
    'python -c "import secondbrain; import secondbrain.knowledge_graph.service; print(secondbrain.__file__)"',
    'python launcher.py version-sync',
    'git diff --exit-code README.md docs/09_MASTERPLAN_STATUS.json',
    'python launcher.py repo-doctor --execute-runtime-checks --write-report',
    'python launcher.py dependency-inventory --write-report',
    'pytest -q -m "(release or connector) and not live and not gui"',
    'pytest -q -m "integration and not live and not gui" tests/integration tests/connectors_runtime tests/storage tests/vision tests/voice',
    'python launcher.py rc-gate --write-report',
)


def _workflow() -> str:
    path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "secondbrain-ci.yml"
    assert path.is_file(), "release CI workflow is missing"
    return path.read_text(encoding="utf-8")


def test_release_workflow_contains_required_commands() -> None:
    content = _workflow()
    missing = [command for command in EXPECTED_COMMANDS if command not in content]
    assert missing == []


def test_release_workflow_has_safe_defaults() -> None:
    content = _workflow()
    assert "contents: read" in content
    assert "cancel-in-progress: true" in content
    assert "timeout-minutes:" in content
    assert 'python-version: ["3.12", "3.13"]' in content
    assert "pull_request:" in content
    assert "workflow_dispatch:" in content


def test_release_workflow_certifies_package_imports_and_knowledge_graph() -> None:
    content = _workflow()
    assert "import secondbrain.knowledge_graph.service" in content
    assert "tests/test_knowledge_graph_persistence.py" in content
    assert "scripts/personal_jarvis_gate.py --project-root ." in content


def test_release_workflow_uploads_only_redacted_reports_and_junit() -> None:
    content = _workflow()
    assert "--junitxml=test-results/" in content
    assert "release/*.json" in content
    assert "runtime/reports/*.json" in content
    assert "test-results/**/*.xml" in content
    assert "*.log" not in content
    assert "persist-credentials: false" in content
