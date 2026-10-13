"""Alle aggregierten Quell-Gates schreiben den commit-gebundenen Umschlag."""
from __future__ import annotations

import pytest

from secondbrain.desktop_native import native_voice_app_gate as voice
from secondbrain.release import jarvis_1_0_gate as aggregator
from secondbrain.release.connector_e2e_gate import run_connector_e2e_gate
from secondbrain.release.evidence import canonical_hash
from secondbrain.release.provider_live_gate import run_provider_live_gate
from secondbrain.release.windows_installer_gate import run_windows_installer_gate

ENVELOPE = {"schema", "commit_sha", "worktree_clean", "environment", "generated_at", "expires_at", "evidence_sha256"}


def _sealed(report: dict) -> bool:
    body = {k: v for k, v in report.items() if k not in {"report", "report_path"}}
    return ENVELOPE <= set(body) and body["evidence_sha256"] == canonical_hash(body)


def test_provider_gate_is_sealed(tmp_path) -> None:
    report = run_provider_live_gate(tmp_path, env={}, write_report=False)
    assert _sealed(report) and report["environment"] == "local"


def test_connector_gate_is_sealed_and_declares_release_scope(tmp_path) -> None:
    report = run_connector_e2e_gate(tmp_path, env={"REQUIRED_E2E_CONNECTORS": "gmail"}, write_report=False)
    assert _sealed(report)
    assert report["release_scope_connectors"] == ["gmail"]


def test_connector_without_release_scope_never_passes_criterion(tmp_path) -> None:
    report = run_connector_e2e_gate(tmp_path, env={}, write_report=False)
    assert report["release_scope_connectors"] == []
    assert not aggregator._criterion_passes("release_connectors_e2e", report)


def test_windows_installer_gate_is_sealed(tmp_path) -> None:
    class Steps:
        def run_phase(self, phase, context):
            return {"name": phase, "status": "SKIPPED", "detail": "", "evidence": {}}

        def cleanup(self):
            pass

    report = run_windows_installer_gate(tmp_path, env={}, steps=Steps(), write_report=False)
    assert _sealed(report)


def test_native_voice_components_cover_every_check() -> None:
    assigned = voice.VOICE_CHECKS + voice.DESKTOP_CHECKS + voice.SHARED_CHECKS
    assert len(assigned) == len(set(assigned)) == 15


@pytest.mark.parametrize("failing,expected", [
    ("voice_input", {"desktop": "PASS", "voice": "BLOCKED"}),
    ("accessibility", {"desktop": "BLOCKED", "voice": "PASS"}),
    ("privacy", {"desktop": "BLOCKED", "voice": "BLOCKED"}),   # Querschnitt betrifft beide
])
def test_native_voice_component_mapping(failing: str, expected: dict) -> None:
    checks = {name: "PASS" for name in voice.VOICE_CHECKS + voice.DESKTOP_CHECKS + voice.SHARED_CHECKS}
    checks[failing] = "BLOCKED"
    assert voice._components(checks) == expected


def test_native_voice_conditional_and_missing_checks_are_not_pass() -> None:
    checks = {name: "PASS" for name in voice.VOICE_CHECKS + voice.DESKTOP_CHECKS + voice.SHARED_CHECKS}
    checks["wake_word"] = "CONDITIONAL_PASS"
    assert voice._components(checks)["voice"] == "CONDITIONAL_PASS"
    del checks["recovery"]
    assert voice._components(checks) == {"desktop": "BLOCKED", "voice": "BLOCKED"}
