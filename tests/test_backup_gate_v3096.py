"""Unit tests for the v30.96 backup gate decision logic.

The real BackupManager (operations_v119, cryptography + PostgreSQL) is exercised
by tests/test_backup_restore_v3096.py and the integration suite. Here we inject
a fake manager to verify only the gate's PASS / CONDITIONAL_PASS / BLOCKED logic
deterministically, without the heavy runtime.
"""

from __future__ import annotations

import pytest

from secondbrain.backup_gate_v3096 import BLOCKED, CONDITIONAL_PASS, PASS, run_backup_gate


class FakeManager:
    def __init__(self, *, create_ok=True, checksums_ok=True, tamper_detected=True,
                 wrong_key_raises=True, restore_ready=True, secret_in_manifest=False):
        self._c = create_ok
        self._ck = checksums_ok
        self._tamper = tamper_detected
        self._wrong_key = wrong_key_raises
        self._ready = restore_ready
        self._secret = secret_in_manifest

    def create(self, *a, **k):
        manifest = {"schema": "secondbrain.backup.manifest.v30_96", "encryption": "AES-256-GCM",
                    "files": [{"path": "db.sql", "sha256": "abc"}]}
        if self._secret:
            manifest["dsn"] = "postgres://user:password@host/db"
        return {"status": "OK" if self._c else "FAILED",
                "backup_id": "bk-1" if self._c else "", "manifest": manifest}

    def verify(self, backup, *, expected_sha256=None, **k):
        if expected_sha256 is not None:  # tamper probe
            return {"checksums_ok": not self._tamper, "manifest_ok": not self._tamper}
        return {"manifest_ok": self._ck, "checksums_ok": self._ck}

    def restore_plan(self, backup, target_dir=None):
        if self._wrong_key is False:
            raise RuntimeError("should_not_be_called")
        return {"status": "READY" if self._ready else "BLOCKED", "dry_run": True}


def _run(mgr):
    return run_backup_gate(".", manager=mgr, write_report=False)


def test_all_good_is_pass():
    report = _run(FakeManager())
    assert report["status"] == PASS
    assert report["summary"]["failed"] == 0


def test_tamper_not_detected_is_blocked():
    report = _run(FakeManager(tamper_detected=False))
    assert report["status"] == BLOCKED
    assert "tamper_rejected" in report["blockers"]


def test_create_failure_is_blocked():
    report = _run(FakeManager(create_ok=False))
    assert report["status"] == BLOCKED
    assert "create" in report["blockers"]


def test_bad_checksums_is_blocked():
    report = _run(FakeManager(checksums_ok=False))
    assert report["status"] == BLOCKED
    assert "checksums" in report["blockers"]


def test_secret_in_manifest_is_blocked():
    report = _run(FakeManager(secret_in_manifest=True))
    assert report["status"] == BLOCKED
    assert "no_secrets_in_manifest" in report["blockers"]


def test_restore_not_ready_is_blocked():
    report = _run(FakeManager(restore_ready=False))
    assert report["status"] == BLOCKED
    assert "restore_roundtrip" in report["blockers"]


def test_report_shape():
    report = _run(FakeManager())
    for key in ("schema", "timestamp", "status", "summary", "checks", "blockers", "warnings", "test_commands"):
        assert key in report
    assert report["schema"] == "secondbrain.backup_gate.v30_96"
    ids = {c["check_id"] for c in report["checks"]}
    assert {"create", "checksums", "tamper_rejected", "wrong_key_rejected",
            "restore_roundtrip", "rollback", "no_secrets_in_manifest"} == ids


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
