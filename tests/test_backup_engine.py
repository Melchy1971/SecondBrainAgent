"""Hermetische und optionale Live-Tests fuer den realen DR-Pfad."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from secondbrain.release import disaster_recovery_gate as drg
from secondbrain.release.backup_engine import (
    BackupError,
    RealRecoverySteps,
    create_encrypted_backup,
    restore_encrypted_backup,
)
from secondbrain.secret_manager.crypto import random_key
from secondbrain.secret_manager.key_provider import b64e


def test_encrypted_filesystem_backup_rejects_wrong_key_and_manifest(tmp_path: Path) -> None:
    source = tmp_path / "config"
    source.mkdir()
    (source / "settings.json").write_text('{"token":"top-secret"}', encoding="utf-8")
    artifact = tmp_path / "backup.enc"
    key = random_key()
    manifest = create_encrypted_backup([source], artifact, key=key)

    restored = tmp_path / "restored"
    result = restore_encrypted_backup(artifact, restored, key=key, manifest=manifest)
    assert result["ok"]
    assert "top-secret" not in artifact.read_text(encoding="utf-8")

    with pytest.raises(BackupError, match="backup_undecryptable"):
        restore_encrypted_backup(
            artifact, tmp_path / "wrong-key", key=random_key(), manifest=manifest
        )
    with pytest.raises(BackupError, match="invalid_backup_manifest"):
        restore_encrypted_backup(
            artifact,
            tmp_path / "bad-manifest",
            key=key,
            manifest={**manifest, "schema": "tampered"},
        )


def test_real_steps_restore_and_rollback_are_isolated(tmp_path: Path) -> None:
    config = tmp_path / "config"
    config.mkdir()
    original = config / "app.json"
    original.write_text('{"mode":"test"}', encoding="utf-8")
    steps = RealRecoverySteps(tmp_path, env={}, key=random_key())
    try:
        report = drg.run_disaster_recovery_gate(
            tmp_path, steps=steps, write_report=False
        )
        assert report["status"] == drg.CONDITIONAL_PASS
        assert all(
            next(c for c in report["checks"] if c["name"] == name)["ok"]
            for name in (
                "full_restore_matches_backup",
                "rollback_restores_prior_state",
                "wrong_key_restore_blocked",
                "tampered_manifest_restore_blocked",
            )
        )
        assert original.read_text(encoding="utf-8") == '{"mode":"test"}'
    finally:
        steps.cleanup()


@pytest.mark.parametrize("failure", ["wrong-key", "manifest"])
def test_broken_restore_blocks_gate_and_rolls_back(
    tmp_path: Path, failure: str
) -> None:
    config = tmp_path / "config"
    config.mkdir()
    (config / "app.json").write_text('{"mode":"before"}', encoding="utf-8")

    class BrokenRestore(RealRecoverySteps):
        def restore(self, backup, project_root):
            manifest = backup["manifest"]
            key = self._master_key()
            if failure == "wrong-key":
                key = random_key()
            else:
                manifest = {**manifest, "schema": "tampered"}
            try:
                restore_encrypted_backup(
                    backup["artifact"],
                    self.restore_target,
                    key=key,
                    manifest=manifest,
                )
            except BackupError:
                return {"ok": False}
            raise AssertionError("broken restore was accepted")

    steps = BrokenRestore(tmp_path, env={}, key=random_key())
    report = drg.run_disaster_recovery_gate(
        tmp_path, steps=steps, write_report=False
    )
    assert report["status"] == drg.BLOCKED
    assert "full_restore_matches_backup" in report["blockers"]
    rollback = next(
        c for c in report["checks"] if c["name"] == "rollback_restores_prior_state"
    )
    assert rollback["ok"]


def test_without_test_database_url_is_skip_never_pass(tmp_path: Path) -> None:
    env = {
        "SECRET_KEY_BACKEND": "env",
        "SECRET_MASTER_KEY_B64": b64e(random_key()),
    }
    report = drg.run_disaster_recovery_gate(
        tmp_path, env=env, write_report=False
    )
    check = next(c for c in report["checks"] if c["name"] == "pg_backup_restore")
    assert not check["ok"]
    assert check["detail"].startswith("SKIP:")
    assert report["status"] == drg.CONDITIONAL_PASS


def test_report_redacts_database_url_and_payload(tmp_path: Path, monkeypatch) -> None:
    secret_dsn = "postgresql://private-user:private-password@db.invalid/secret-db"
    monkeypatch.setattr("secondbrain.release.backup_engine.pg_tools_available", lambda: False)
    env = {
        "TEST_DATABASE_URL": secret_dsn,
        "SECRET_KEY_BACKEND": "env",
        "SECRET_MASTER_KEY_B64": b64e(random_key()),
    }
    report = drg.run_disaster_recovery_gate(tmp_path, env=env, write_report=False)
    serialized = json.dumps(report)
    for secret in ("private-user", "private-password", "db.invalid", "secret-db"):
        assert secret not in serialized


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"),
    reason="set TEST_DATABASE_URL for real pg_dump/pg_restore",
)
def test_real_pg_dump_restore_roundtrip(tmp_path: Path) -> None:
    env = {
        "TEST_DATABASE_URL": os.environ["TEST_DATABASE_URL"],
        "SECRET_KEY_BACKEND": "env",
        "SECRET_MASTER_KEY_B64": b64e(random_key()),
    }
    report = drg.run_disaster_recovery_gate(tmp_path, env=env, write_report=False)
    assert report["status"] == drg.PASS, report
    for name in (
        "pg_dump_real",
        "pg_restore_into_empty_database",
        "restored_row_counts_match",
        "restored_checksums_match",
        "pgvector_golden_recall",
        "approval_integrity",
        "audit_integrity_no_gap",
        "failed_restore_blocked",
        "failed_restore_atomic_rollback",
    ):
        assert next(c for c in report["checks"] if c["name"] == name)["ok"]
