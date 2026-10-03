"""Disaster-Recovery-Gate: echter Krypto-Nachweis plus Orchestrierung.

Der Kryptografieteil laeuft gegen die reale AES-GCM-Implementierung. Die
Backup-/Restore-Orchestrierung wird ueber injizierte Schritte geprueft, ohne
echtes Dateisystem-Backup -- die Fehlerfaelle (Datenverlust, fehlender
Rollback, ungueltige Checksumme) sind so deterministisch ausloesbar.
"""

from __future__ import annotations

import json

import pytest

from secondbrain.release import disaster_recovery_gate as drg


# --------------------------------------------------------------------------
# Kryptografie -- real
# --------------------------------------------------------------------------


def _named(report, name: str) -> dict:
    for check in report["checks"]:
        if check["name"] == name:
            return check
    raise AssertionError(f"Pruefung {name!r} fehlt")


def test_crypto_self_test_passes_against_real_implementation() -> None:
    report = drg.run_disaster_recovery_gate(
        ".", steps=drg.RecoverySteps(), write_report=False
    )
    for name in (
        "encrypted_backup_roundtrip",
        "wrong_key_is_rejected",
        "tampered_backup_is_rejected",
        "vault_artifact_has_no_plaintext",
        "aad_context_binding",
        "key_rotation_preserves_data",
    ):
        assert _named(report, name)["ok"], f"{name} fehlgeschlagen"


def test_healthy_run_is_conditional_pass_not_pass() -> None:
    """Delegierte DB-Checks stehen aus -> nie PASS in dieser Stufe.

    Hermetisch: injizierte Fake-Schritte, damit der Kontrollfluss ohne echtes
    Backend und ohne Master-Key prueft.
    """
    report = drg.run_disaster_recovery_gate(".", steps=drg.RecoverySteps(), write_report=False)
    assert report["status"] == drg.CONDITIONAL_PASS
    assert set(report["delegated_checks"]) == set(drg.DELEGATED_CHECKS)
    assert report["steps"] == "injected"


# --------------------------------------------------------------------------
# Orchestrierung -- injizierte Schritte
# --------------------------------------------------------------------------


def _run(steps):
    return drg.run_disaster_recovery_gate(".", steps=steps, write_report=False)


def test_full_recovery_cycle_passes() -> None:
    report = _run(drg.RecoverySteps())
    for name in ("snapshot_before_restore", "full_backup", "backup_checksum_valid",
                 "full_restore_matches_backup", "rollback_restores_prior_state"):
        assert _named(report, name)["ok"], f"{name} fehlgeschlagen"


def test_restore_that_loses_data_is_blocked() -> None:
    class LossyRestore(drg.RecoverySteps):
        def restore(self, backup, project_root):
            return {"ok": True, "checksum": "something-else"}  # weicht vom Backup ab

    report = _run(LossyRestore())
    assert report["status"] == drg.BLOCKED
    assert "full_restore_matches_backup" in report["blockers"]


def test_missing_rollback_is_blocked() -> None:
    class NoRollback(drg.RecoverySteps):
        def rollback(self, snapshot, project_root):
            return {"ok": False}

    report = _run(NoRollback())
    assert report["status"] == drg.BLOCKED
    assert "rollback_restores_prior_state" in report["blockers"]


def test_invalid_checksum_is_blocked() -> None:
    class NoChecksum(drg.RecoverySteps):
        def create_backup(self, project_root):
            return {"ok": True, "checksum": "", "artifact": "b.enc"}

    report = _run(NoChecksum())
    assert report["status"] == drg.BLOCKED
    assert "backup_checksum_valid" in report["blockers"]


def test_failed_backup_is_blocked() -> None:
    class NoBackup(drg.RecoverySteps):
        def create_backup(self, project_root):
            return {"ok": False}

    report = _run(NoBackup())
    assert report["status"] == drg.BLOCKED
    assert "full_backup" in report["blockers"]


def test_rollback_targets_prior_state_not_backup() -> None:
    """Rollback stellt den Vorzustand her, nicht den Backup-Zustand."""
    seen = {}

    class Tracking(drg.RecoverySteps):
        def snapshot_state(self, project_root):
            return {"ok": True, "checksum": "prior"}

        def rollback(self, snapshot, project_root):
            seen["target"] = snapshot.get("checksum")
            return {"ok": True, "checksum": snapshot.get("checksum")}

    report = _run(Tracking())
    assert seen["target"] == "prior"
    assert _named(report, "rollback_restores_prior_state")["ok"]


# --------------------------------------------------------------------------
# Redaktion
# --------------------------------------------------------------------------


def test_report_contains_no_secret_material() -> None:
    report = drg.run_disaster_recovery_gate(
        ".", steps=drg.RecoverySteps(), write_report=False
    )
    blob = json.dumps(report)
    # Die Krypto-Nutzlast enthielt genau diese Marker -- keiner darf auftauchen.
    for secret in ("do-not-log", "token=", "ws-a"):
        assert secret not in blob, f"{secret!r} steht im Report"


def test_step_exception_is_contained() -> None:
    class Exploding(drg.RecoverySteps):
        def create_backup(self, project_root):
            raise RuntimeError("disk full")

    report = drg.run_disaster_recovery_gate(".", steps=Exploding(), write_report=False)
    assert report["status"] == drg.BLOCKED
    assert "disk full" not in json.dumps(report)
