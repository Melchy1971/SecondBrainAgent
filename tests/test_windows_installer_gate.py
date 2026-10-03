"""Hermetic control-flow tests for the Windows installer gate."""

from __future__ import annotations

import json
from pathlib import Path

import launcher

from secondbrain.release import windows_installer_gate as gate


class FakeSteps:
    def __init__(self, statuses: dict[str, str] | None = None) -> None:
        self.statuses = statuses or {}
        self.calls: list[str] = []
        self.cleaned = False

    def run_phase(self, phase: str, context: dict) -> dict:
        self.calls.append(phase)
        return {
            "name": phase,
            "status": self.statuses.get(phase, gate.PASS),
            "detail": "ok",
            "evidence": (
                {"artifacts": [{"name": "Jarvis-Setup.exe", "bytes": 42}]}
                if phase == "artifact_inventory" else {}
            ),
        }

    def cleanup(self) -> None:
        self.cleaned = True


def test_all_phases_pass_in_declared_order() -> None:
    steps = FakeSteps()
    report = gate.run_windows_installer_gate(".", steps=steps, write_report=False)
    assert report["status"] == gate.PASS
    assert steps.calls == list(gate.PHASES)
    assert [row["name"] for row in report["phases"]] == list(gate.PHASES)
    assert steps.cleaned


def test_missing_vm_is_skipped_never_pass() -> None:
    steps = FakeSteps({"preflight": gate.SKIPPED})
    report = gate.run_windows_installer_gate(".", steps=steps, write_report=False)
    assert report["status"] == gate.SKIPPED
    assert not report["ok"]
    assert all(
        row["status"] == gate.SKIPPED
        for row in report["phases"]
        if row["name"] not in {"preflight", "report"}
    )


def test_missing_certificate_blocks_and_halts() -> None:
    steps = FakeSteps({"signature_verification": gate.BLOCKED})
    report = gate.run_windows_installer_gate(".", steps=steps, write_report=False)
    assert report["status"] == gate.BLOCKED
    assert "signature_verification" in report["blockers"]
    install = next(row for row in report["phases"] if row["name"] == "silent_install")
    assert install["status"] == gate.SKIPPED


def test_live_preflight_missing_certificate_is_blocked(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(gate.sys, "platform", "win32")
    steps = gate.LiveWindowsInstallerSteps(
        tmp_path,
        env={"WINDOWS_INSTALLER_GATE_ISOLATION": "clean-vm"},
    )
    row = steps.run_phase("preflight", {})
    assert row["status"] == gate.BLOCKED
    assert row["detail"] == "code-signing certificate missing"


def test_live_preflight_missing_isolation_is_skipped(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(gate.sys, "platform", "win32")
    steps = gate.LiveWindowsInstallerSteps(
        tmp_path,
        env={"WINDOWS_SIGNING_CERT_THUMBPRINT": "AA"},
    )
    row = steps.run_phase("preflight", {})
    assert row["status"] == gate.SKIPPED


def test_every_certification_phase_is_required_for_pass() -> None:
    for phase in gate.PHASES[:-1]:
        report = gate.run_windows_installer_gate(
            ".", steps=FakeSteps({phase: gate.BLOCKED}), write_report=False
        )
        assert report["status"] == gate.BLOCKED, phase


def test_exception_is_redacted_and_cleanup_runs() -> None:
    class Exploding(FakeSteps):
        def run_phase(self, phase, context):
            if phase == "clean_build":
                raise RuntimeError(r"C:\Users\Alice\secret-token.txt")
            return super().run_phase(phase, context)

    steps = Exploding()
    report = gate.run_windows_installer_gate(".", steps=steps, write_report=False)
    serialized = json.dumps(report)
    assert report["status"] == gate.BLOCKED
    assert "Alice" not in serialized
    assert "secret-token" not in serialized
    assert steps.cleaned


def test_report_is_atomic_machine_readable_and_path_redacted(tmp_path: Path) -> None:
    report = gate.run_windows_installer_gate(tmp_path, steps=FakeSteps())
    target = tmp_path / gate.REPORT_PATH
    persisted = json.loads(target.read_text(encoding="utf-8"))
    assert persisted["status"] == gate.PASS
    assert report["report"] == gate.REPORT_PATH.as_posix()
    assert not list(target.parent.glob("*.tmp"))
    assert str(tmp_path) not in json.dumps(persisted)


def test_launcher_command_exists_and_returns_nonzero_without_windows(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    monkeypatch.setattr(
        gate,
        "run_windows_installer_gate",
        lambda *args, **kwargs: {"status": gate.SKIPPED},
    )
    code = launcher.main([
        "windows-installer-gate", "--project-root", str(tmp_path),
        "--no-write-report",
    ])
    assert code == 2
    assert json.loads(capsys.readouterr().out)["status"] == gate.SKIPPED
