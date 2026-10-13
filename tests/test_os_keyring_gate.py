"""OS-Keyring-Gate mit simuliertem Keyring (der Live-Lauf nutzt den echten)."""
from __future__ import annotations

import json

import pytest

from secondbrain.release import jarvis_1_0_gate as aggregator
from secondbrain.release import os_keyring_gate as gate
from secondbrain.secret_manager.key_provider import EnvKeyProvider, OSKeyringKeyProvider


class FakeKeyring(OSKeyringKeyProvider):
    def __init__(self, service: str, *, available: bool = True, forget_delete: bool = False) -> None:
        super().__init__(service=service)
        self.store: dict[str, str] = {}
        self._available = available
        self.forget_delete = forget_delete

    def available(self) -> bool:
        return self._available

    def _get(self, alias):
        return self.store.get(alias)

    def _set(self, alias, value):
        self.store[alias] = value

    def _delete(self, alias):
        if not self.forget_delete:
            self.store.pop(alias, None)

    def health(self):
        return {"keyring_backend": "FakeKeyring"}


def _run(monkeypatch, tmp_path, *, provider=None, **fake):
    created: list[FakeKeyring] = []
    monkeypatch.setattr(gate, "resolve_key_provider", lambda _env: provider or FakeKeyring("prod"))

    def factory(service):
        created.append(FakeKeyring(service, **fake))
        return created[-1]

    report = gate.run_os_keyring_gate(tmp_path, env={}, keyring_factory=factory, write_report=False)
    return report, created


def test_secure_backend_with_roundtrip_passes(monkeypatch, tmp_path) -> None:
    report, created = _run(monkeypatch, tmp_path)
    assert report["status"] == gate.PASS
    assert aggregator._criterion_passes("os_keyring", report)
    assert created[0].store == {}, "Gate-Eintrag muss entfernt sein"
    assert created[0].service.startswith("secondbrain-gate-")


def test_env_backend_is_not_secure(monkeypatch, tmp_path) -> None:
    report, _ = _run(monkeypatch, tmp_path, provider=EnvKeyProvider({}))
    assert report["status"] == gate.BLOCKED
    assert report["backend"] == "env" and report["secure_backend"] is False
    assert not aggregator._criterion_passes("os_keyring", report)


def test_unavailable_keyring_blocks(monkeypatch, tmp_path) -> None:
    report, _ = _run(monkeypatch, tmp_path, available=False)
    row = next(c for c in report["checks"] if c["name"] == "keyring_roundtrip")
    assert (row["ok"], report["status"]) == (False, gate.BLOCKED)


def test_failed_cleanup_blocks(monkeypatch, tmp_path) -> None:
    report, _ = _run(monkeypatch, tmp_path, forget_delete=True)
    assert next(c for c in report["checks"] if c["name"] == "keyring_cleanup")["ok"] is False
    assert report["status"] == gate.BLOCKED


def test_report_never_contains_key_material(monkeypatch, tmp_path) -> None:
    seen: list[str] = []

    class Spy(FakeKeyring):
        def _set(self, alias, value):
            seen.append(value)
            super()._set(alias, value)

    monkeypatch.setattr(gate, "resolve_key_provider", lambda _env: FakeKeyring("prod"))
    report = gate.run_os_keyring_gate(tmp_path, env={}, keyring_factory=lambda s: Spy(s), write_report=False)
    assert seen and seen[0] not in json.dumps(report)


@pytest.mark.parametrize("cmd", ["os-keyring-gate"])
def test_launcher_command_exists(monkeypatch, tmp_path, capsys, cmd) -> None:
    import launcher

    monkeypatch.setattr(gate, "run_os_keyring_gate", lambda *a, **k: {"status": gate.BLOCKED})
    assert launcher.main([cmd, "--project-root", str(tmp_path), "--no-write-report"]) == 2
    assert json.loads(capsys.readouterr().out)["status"] == gate.BLOCKED
