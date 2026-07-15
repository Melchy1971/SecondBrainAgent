from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from secondbrain.operations_v119 import (
    BackupError,
    BackupManager,
    BackupScheduler,
    RestoreWizard,
)


BACKUP_KEY = base64.b64encode(bytes(range(32))).decode("ascii")


def _project(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "project"
    runtime = root / "runtime"
    (root / "config").mkdir(parents=True)
    (root / "config" / "settings.json").write_text('{"mode":"production"}', encoding="utf-8")
    (root / ".env").write_text("API_TOKEN=must-remain-encrypted\n", encoding="utf-8")
    (root / "memory").mkdir()
    (root / "memory" / "facts.jsonl").write_text('{"fact":"kept"}\n', encoding="utf-8")
    (runtime / "vault").mkdir(parents=True)
    (runtime / "vault" / "vault.json").write_text('{"ciphertext":"already-encrypted"}', encoding="utf-8")
    (runtime / "native").mkdir()
    (runtime / "native" / "approvals.jsonl").write_text('{"status":"pending"}\n', encoding="utf-8")
    (runtime / "connectors").mkdir()
    (runtime / "connectors" / "checkpoint.json").write_text('{"cursor":"42"}', encoding="utf-8")
    (runtime / "audit").mkdir()
    (runtime / "audit" / "events.jsonl").write_text('{"event":"created"}\n', encoding="utf-8")
    (runtime / "logs").mkdir()
    (runtime / "logs" / "app.log").write_text("ready", encoding="utf-8")
    return root, runtime


def _manager(tmp_path: Path, **env: str) -> BackupManager:
    root, runtime = _project(tmp_path)
    return BackupManager(root, runtime, env={"SECONDBRAIN_BACKUP_KEY": BACKUP_KEY, **env})


def test_encrypted_versioned_backup_covers_governed_components(tmp_path: Path) -> None:
    manager = _manager(tmp_path)

    backup = manager.create(encrypt=True, include_database=False, label="nightly")
    raw = Path(backup["path"]).read_bytes()
    verification = manager.verify(backup["backup_id"])

    assert Path(backup["path"]).suffix == ".sbbackup"
    assert raw.startswith(manager.ENCRYPTED_MAGIC)
    assert b"already-encrypted" not in raw
    assert b"must-remain-encrypted" not in raw
    assert backup["version"] == "30.96"
    assert backup["encryption"] == "AES-256-GCM"
    assert verification["ok"] is True
    assert {"configuration", "memory", "secret_vault", "approval_queue", "connector_checkpoints", "audit", "logs"}.issubset(
        set(verification["manifest"]["components"])
    )


def test_restore_roundtrip_validates_every_file_and_rollback_is_lossless(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    source = manager.project_root / "memory" / "facts.jsonl"
    original = source.read_bytes()
    backup = manager.create(encrypt=True, include_database=False)
    wizard = RestoreWizard(manager)
    target = tmp_path / "restore_roundtrip"

    dry_run = wizard.dry_run(backup["backup_id"], target)
    restored = wizard.restore(backup["backup_id"], target)

    assert dry_run["status"] == "READY"
    assert restored["status"] == "COMPLETED"
    assert restored["restore_validation"]["ok"] is True
    assert (target / "project" / "memory" / "facts.jsonl").read_bytes() == original
    assert source.read_bytes() == original

    rolled_back = wizard.rollback()
    assert rolled_back["rolled_back"] is True
    assert not target.exists()
    assert source.read_bytes() == original


def test_corrupted_encrypted_backup_is_rejected_without_target_mutation(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    backup = manager.create(encrypt=True, include_database=False)
    backup_path = Path(backup["path"])
    raw = bytearray(backup_path.read_bytes())
    raw[len(raw) // 2] ^= 0x01
    backup_path.write_bytes(raw)
    target = tmp_path / "restore_corrupt"

    validation = manager.verify(str(backup_path))

    assert validation["ok"] is False
    assert "backup_authentication_failed" in validation["errors"]
    with pytest.raises(BackupError):
        manager.restore(str(backup_path), target)
    assert not target.exists()


def test_restore_validation_detects_post_restore_damage(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    backup = manager.create(encrypt=True, include_database=False)
    target = tmp_path / "restore_validate"
    manager.restore(backup["backup_id"], target)
    restored_file = target / "project" / "config" / "settings.json"
    restored_file.write_text("corrupted", encoding="utf-8")

    validation = manager.validate_restored_target(backup["backup_id"], target)

    assert validation["ok"] is False
    assert validation["errors"] == ["restored_file_hash_mismatch"]


def test_scheduler_creates_only_one_backup_per_interval(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    scheduler = BackupScheduler(manager)
    scheduler.configure(interval="daily", enabled=True)
    now = datetime(2026, 7, 14, tzinfo=timezone.utc)

    first = scheduler.run_due(now=now)
    second = scheduler.run_due(now=now + timedelta(hours=2))

    assert first["created"] is True
    assert second == {"status": "not_due", "created": False, "last_backup_id": first["backup"]["backup_id"]}
    assert len(manager.list()) == 1


def test_postgres_and_pgvector_dump_is_included_without_dsn_leak(tmp_path: Path) -> None:
    root, runtime = _project(tmp_path)
    calls: list[tuple[list[str], dict[str, str]]] = []

    def runner(command, *, env, **_kwargs):
        calls.append((list(command), dict(env)))
        Path(command[command.index("--file") + 1]).write_bytes(b"PGDMP pgvector data")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    secret = "database-password-must-not-leak"
    manager = BackupManager(
        root,
        runtime,
        env={
            "SECONDBRAIN_BACKUP_KEY": BACKUP_KEY,
            "DATABASE_URL": f"postgresql://backup:{secret}@localhost:5432/secondbrain",
        },
        command_runner=runner,
    )

    backup = manager.create(encrypt=True)
    verification = manager.verify(backup["backup_id"])

    assert calls and secret not in " ".join(calls[0][0])
    assert calls[0][1]["PGPASSWORD"] == secret
    assert verification["manifest"]["database"]["status"] == "created"
    assert "postgresql" in verification["manifest"]["components"]
    assert "pgvector" in verification["manifest"]["components"]
    assert secret not in manager.index_path.read_text(encoding="utf-8")


def test_health_and_report_are_secret_free(tmp_path: Path) -> None:
    manager = _manager(tmp_path)
    manager.create(encrypt=True, include_database=False)

    health = manager.health()
    report = manager.write_report()
    serialized = json.dumps(report)

    assert health["status"] == "PASS"
    assert report["health"]["status"] == "PASS"
    assert Path(report["path"]).exists()
    assert BACKUP_KEY not in serialized


def test_production_rejects_unencrypted_backup(tmp_path: Path) -> None:
    root, runtime = _project(tmp_path)
    manager = BackupManager(root, runtime, env={"SECONDBRAIN_ENV": "production"})

    with pytest.raises(BackupError, match="unencrypted_backup_blocked_in_production"):
        manager.create(encrypt=False, include_database=False)
