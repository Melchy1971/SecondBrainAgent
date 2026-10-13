"""Hermetische und optionale Live-Tests fuer den realen DR-Pfad."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from secondbrain.release import backup_engine as be
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
        "DR_RESTORE_TEMPLATE": os.environ.get("DR_RESTORE_TEMPLATE", "template0"),
        "SECRET_KEY_BACKEND": "env",
        "SECRET_MASTER_KEY_B64": b64e(random_key()),
    }
    report = drg.run_disaster_recovery_gate(tmp_path, env=env, write_report=False)
    assert report["status"] == drg.PASS, report
    for name in (
        "pg_tls_verify_full",
        "pg_dump_real",
        "restore_target_empty_before_restore",
        "pg_restore_into_empty_database",
        "restored_row_counts_match",
        "restored_checksums_match",
        "pgvector_golden_recall",
        "approval_integrity",
        "audit_integrity_no_gap",
        "failed_restore_blocked",
        "failed_restore_mid_restore",
        "failed_restore_atomic_rollback",
    ):
        assert next(c for c in report["checks"] if c["name"] == name)["ok"]


# --------------------------------------------------------------------------
# Hermetisch: TLS-Weitergabe, Fehlerinjektion, Fortschrittsauswertung
# --------------------------------------------------------------------------



def test_pg_env_passes_tls_parameters_to_libpq_tools() -> None:
    env = be._pg_env("postgresql://u:pw@db.example:6543/app?sslmode=verify-full&sslrootcert=/certs/ca.crt")
    assert env["PGSSLMODE"] == "verify-full"
    assert env["PGSSLROOTCERT"] == "/certs/ca.crt"
    assert (env["PGHOST"], env["PGPORT"], env["PGDATABASE"]) == ("db.example", "6543", "app")


@pytest.mark.parametrize("dsn,mode", [
    ("postgresql://u:pw@db.example/app?sslmode=require", "require"),
    ("postgresql://u:pw@db.example/app", "prefer"),
])
def test_database_checks_require_verify_full(tmp_path: Path, monkeypatch, dsn: str, mode: str) -> None:
    monkeypatch.setattr(be, "pg_tools_available", lambda: True)
    monkeypatch.delenv("PGSSLMODE", raising=False)
    steps = RealRecoverySteps(tmp_path, env={"TEST_DATABASE_URL": dsn}, key=random_key(),
                              run=lambda *a, **k: pytest.fail("no tool may run without verify-full"))
    checks = steps.database_checks(tmp_path)
    assert checks == [{"name": "pg_tls_verify_full", "ok": False,
                       "detail": f"sslmode={mode}; verify-full required", "blocking": True}]


def test_corrupt_last_table_data_targets_last_fixture_table(tmp_path: Path) -> None:
    listing = (
        ";\n; Archive created\n"
        "3401; 0 16400 TABLE DATA sb_dr_fx_ab dr_approvals gate\n"
        "3402; 0 16410 TABLE DATA sb_dr_fx_ab dr_audit gate\n"
        "3403; 0 16420 TABLE DATA sb_dr_fx_ab dr_vectors gate\n"
        "3404; 0 16430 TABLE DATA public unrelated gate\n"
    )
    for dump_id in ("3401", "3402", "3403", "3404"):
        (tmp_path / f"{dump_id}.dat").write_text("1\t[1,0,0]\n\\.\n\n", encoding="utf-8", newline="\n")
    table = be._corrupt_last_table_data(tmp_path, listing, "sb_dr_fx_ab")
    assert table == "dr_vectors"
    assert "corrupt-row-without-columns\n\\.\n" in (tmp_path / "3403.dat").read_text(encoding="utf-8")
    for untouched in ("3401", "3402", "3404"):
        assert "corrupt" not in (tmp_path / f"{untouched}.dat").read_text(encoding="utf-8")


def test_corrupt_requires_earlier_table_data(tmp_path: Path) -> None:
    listing = "3403; 0 16420 TABLE DATA sb_dr_fx_ab dr_vectors gate\n"
    (tmp_path / "3403.dat").write_text("\\.\n", encoding="utf-8")
    with pytest.raises(BackupError, match="fixture_table_data_missing"):
        be._corrupt_last_table_data(tmp_path, listing, "sb_dr_fx_ab")


def test_restore_progress_excludes_the_failing_block() -> None:
    log = (
        'pg_restore: creating TABLE "s.dr_approvals"\n'
        'pg_restore: creating TABLE "s.dr_audit"\n'
        'pg_restore: processing data for table "s.dr_approvals"\n'
        'pg_restore: processing data for table "s.dr_audit"\n'
        'pg_restore: processing data for table "s.dr_vectors"\n'
        "pg_restore: error: COPY failed for table \"dr_vectors\"\n"
    )
    assert be._restore_progress(log) == {"created_tables": 2, "completed_data": 2}
    assert be._restore_progress("") == {"created_tables": 0, "completed_data": 0}


def test_fixture_sql_rejects_unsafe_schema_names() -> None:
    assert "CREATE SCHEMA sb_dr_fx_ab12;" in be._fixture_sql("sb_dr_fx_ab12")
    with pytest.raises(BackupError, match="invalid_fixture_schema"):
        be._fixture_sql("x; DROP DATABASE prod")


def test_restore_works_without_tarfile_data_filter(tmp_path: Path, monkeypatch) -> None:
    """Python 3.11.0-3.11.3 kennt filter="data" nicht -- Restore darf nicht abbrechen."""
    import tarfile

    source = tmp_path / "config"
    source.mkdir()
    (source / "a.json").write_text("{}", encoding="utf-8")
    key = random_key()
    manifest = create_encrypted_backup([source], tmp_path / "b.enc", key=key)
    monkeypatch.delattr(tarfile, "data_filter", raising=False)  # fehlt auf Python < 3.11.4
    calls: list[dict] = []
    original = tarfile.TarFile.extractall

    def strict_extractall(self, path=".", members=None, *, numeric_owner=False, **kwargs):
        calls.append(kwargs)
        assert "filter" not in kwargs, "filter darf auf altem Python nicht uebergeben werden"
        return original(self, path, members, numeric_owner=numeric_owner)

    monkeypatch.setattr(tarfile.TarFile, "extractall", strict_extractall)
    assert restore_encrypted_backup(tmp_path / "b.enc", tmp_path / "out", key=key, manifest=manifest)["ok"]
    assert calls == [{}]


def test_safe_members_rejects_special_files(tmp_path: Path) -> None:
    import io
    import tarfile

    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        fifo = tarfile.TarInfo("artifact-0/pipe")
        fifo.type = tarfile.FIFOTYPE
        tar.addfile(fifo)
    buffer.seek(0)
    with tarfile.open(fileobj=buffer) as tar, pytest.raises(BackupError, match="backup_special_files_forbidden"):
        be._safe_members(tar, tmp_path)


def test_skip_present_extensions_only_comments_out_existing_ones() -> None:
    listing = (
        "; Archive\n"
        "3416; 3079 16385 EXTENSION - vector \n"
        "3417; 0 0 COMMENT - EXTENSION vector \n"
        "3418; 3079 16390 EXTENSION - pgcrypto \n"
        "3419; 1259 16400 TABLE s dr_vectors gate\n"
    )
    filtered, skipped = be._skip_present_extensions(listing, {"vector"})
    assert skipped == ["vector", "vector"]
    lines = filtered.splitlines()
    assert lines[1].startswith(";3416") and lines[2].startswith(";3417")
    assert lines[3].startswith("3418") and lines[4].startswith("3419")
    assert be._skip_present_extensions(listing, set())[1] == []


def test_restore_template_is_validated(tmp_path: Path) -> None:
    ok = RealRecoverySteps(tmp_path, env={"DR_RESTORE_TEMPLATE": "sb_dr_template"}, key=random_key())
    assert ok._restore_template() == "sb_dr_template"
    assert RealRecoverySteps(tmp_path, env={}, key=random_key())._restore_template() == "template0"
    bad = RealRecoverySteps(tmp_path, env={"DR_RESTORE_TEMPLATE": "x; DROP"}, key=random_key())
    with pytest.raises(BackupError, match="invalid_restore_template"):
        bad._restore_template()


def test_diagnose_gives_hint_without_leaking_tool_output() -> None:
    import subprocess

    exc = subprocess.CalledProcessError(1, ["pg_restore"], stderr=(
        'pg_restore: error: connection to "db.internal" ... '
        'ERROR:  permission denied to create extension "vector"'))
    detail = be._diagnose(exc)
    assert detail.startswith("CalledProcessError: ") and "DR_RESTORE_TEMPLATE" in detail
    assert "db.internal" not in detail
    assert be._diagnose(RuntimeError("secret host")) == "RuntimeError"
