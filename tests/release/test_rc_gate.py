"""Tests for the v30.80 release-candidate gate (Task 7)."""

from __future__ import annotations

import json

from secondbrain.release.rc_gate import (
    CheckResult,
    CheckStatus,
    GateContext,
    Verdict,
    check_connector_runtime,
    check_embedding_provider,
    check_repo_doctor,
    check_secret_vault,
    decide_verdict,
    run_rc_gate,
    write_artifacts,
)


def _r(name, status, critical=False):
    return CheckResult(name, status, f"{name} {status.value}", critical=critical,
                       file="f", cause="c", remediation="fix")


# --- verdict logic -------------------------------------------------------------

def test_all_pass_is_pass():
    assert decide_verdict([_r("a", CheckStatus.PASS), _r("b", CheckStatus.PASS)]) is Verdict.PASS


def test_warn_is_conditional_pass():
    assert decide_verdict([_r("a", CheckStatus.PASS), _r("b", CheckStatus.WARN)]) is Verdict.CONDITIONAL_PASS


def test_any_fail_is_blocked():
    assert decide_verdict([_r("a", CheckStatus.PASS), _r("b", CheckStatus.FAIL)]) is Verdict.BLOCKED


# --- hard rules ----------------------------------------------------------------

def test_dev_only_embeddings_block_release():
    def dev_only_embed(ctx):
        return _r("embedding_provider", CheckStatus.FAIL, critical=True)
    report = run_rc_gate(".", checks=[lambda c: _r("x", CheckStatus.PASS), dev_only_embed])
    assert report["verdict"] == Verdict.BLOCKED.value
    assert report["blockers"][0]["name"] == "embedding_provider"
    assert report["blockers"][0]["critical"] is True


def test_missing_vault_blocks(tmp_path):
    # run in an empty dir: vault package still importable, but embedding + others fail
    report = run_rc_gate(tmp_path)
    assert report["verdict"] == Verdict.BLOCKED.value


def test_real_secret_vault_check_passes():
    assert check_secret_vault(_ctx()).status is CheckStatus.PASS


def test_real_connector_runtime_check_passes():
    assert check_connector_runtime(_ctx()).status is CheckStatus.PASS


def test_embedding_check_flags_dev_only_as_critical(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "vector_rag.yaml").write_text("provider: local\n", encoding="utf-8")
    from secondbrain.release.rc_gate import GateContext
    from pathlib import Path

    result = check_embedding_provider(GateContext(project_root=Path(tmp_path), target_version="test"))
    assert result.status is CheckStatus.FAIL
    assert result.critical is True
    assert result.remediation and "semantic" in result.remediation


def test_repo_doctor_uses_packaged_module_case(tmp_path):
    (tmp_path / "SecondBrain").mkdir()
    (tmp_path / "launcher.py").write_text("", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("", encoding="utf-8")

    result = check_repo_doctor(GateContext(project_root=tmp_path, target_version="test"))

    assert result.status is CheckStatus.WARN


# --- artifacts -----------------------------------------------------------------

def test_write_artifacts_creates_json_and_markdown(tmp_path):
    report = run_rc_gate(".", checks=[
        lambda c: _r("ok", CheckStatus.PASS),
        lambda c: CheckResult("emb", CheckStatus.FAIL, "dev only", critical=True,
                              file=".env", cause="deterministic", remediation="use openai"),
    ])
    write_artifacts(report, tmp_path)
    data = json.loads((tmp_path / "release" / "rc_status_latest.json").read_text(encoding="utf-8"))
    assert data["verdict"] == "BLOCKED"
    md = (tmp_path / "docs" / "releases" / "v30_80_rc_report.md").read_text(encoding="utf-8")
    assert "BLOCKED" in md
    assert "Datei:" in md and "Ursache:" in md and "MaÃŸnahme:" in md
    assert "`.env`" in md


def test_report_has_fifteen_default_checks():
    report = run_rc_gate(".")
    assert report["summary"]["total"] == 15
    names = {c["name"] for c in report["checks"]}
    assert {"version_sync", "secret_vault", "connector_runtime", "embedding_provider",
            "installer_build", "pytest"} <= names


def _ctx():
    from secondbrain.release.rc_gate import GateContext
    from pathlib import Path
    return GateContext(project_root=Path("."), target_version="30.80.0")
