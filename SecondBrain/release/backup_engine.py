"""Isolierter, verschluesselter Disaster-Recovery-Pfad.

Dateiartefakte werden mit dem Phase-A-Master-Key verschluesselt. PostgreSQL
wird ausschliesslich ueber TEST_DATABASE_URL angesprochen; Restore-Ziele sind
frisch erzeugte, temporaere Datenbanken auf demselben Testserver.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import urlsplit
from uuid import uuid4

from secondbrain.secret_manager.crypto import decrypt, encrypt, random_key

MANIFEST_SCHEMA = "secondbrain.dr.backup.manifest.v1"
_AAD = b"secondbrain-dr-backup-v1"
_DB_PREFIX = "sb_dr_"
_TOOLS = ("pg_dump", "pg_restore", "psql", "createdb", "dropdb")


class BackupError(RuntimeError):
    """Redigierter Backup-/Restore-Fehler."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _tree_checksum(path: Path) -> str:
    digest = hashlib.sha256()
    if path.exists():
        for item in sorted(p for p in path.rglob("*") if p.is_file()):
            digest.update(item.relative_to(path).as_posix().encode())
            digest.update(item.read_bytes())
    return digest.hexdigest()


def _safe_members(tar: tarfile.TarFile, destination: Path) -> list[tarfile.TarInfo]:
    root = destination.resolve()
    members = tar.getmembers()
    for member in members:
        target = (root / member.name).resolve()
        if root != target and root not in target.parents:
            raise BackupError("unsafe_backup_member")
        if member.issym() or member.islnk():
            raise BackupError("backup_links_forbidden")
    return members


def create_encrypted_backup(sources: list[Path], out_path: Path, *, key: bytes) -> dict[str, Any]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    present = [source for source in sources if source.exists()]
    with tempfile.TemporaryDirectory() as temp:
        archive = Path(temp) / "payload.tar"
        with tarfile.open(archive, "w") as tar:
            for index, source in enumerate(present):
                tar.add(source, arcname=f"artifact-{index}/{source.name}", recursive=True)
        encrypted = encrypt(key, archive.read_bytes(), aad=_AAD)
    serialized = json.dumps(encrypted, separators=(",", ":")).encode()
    out_path.write_bytes(serialized)
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "artifact": out_path.name,
        "ciphertext_sha256": _sha256(serialized),
        "content_sha256": _tree_checksum_from_sources(present),
        "source_count": len(present),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    out_path.with_suffix(out_path.suffix + ".manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


def _tree_checksum_from_sources(sources: list[Path]) -> str:
    digest = hashlib.sha256()
    for index, source in enumerate(sources):
        if source.is_file():
            digest.update(f"artifact-{index}/{source.name}".encode())
            digest.update(source.read_bytes())
        else:
            for item in sorted(p for p in source.rglob("*") if p.is_file()):
                name = Path(f"artifact-{index}/{source.name}") / item.relative_to(source)
                digest.update(name.as_posix().encode())
                digest.update(item.read_bytes())
    return digest.hexdigest()


def restore_encrypted_backup(
    artifact: Path, destination: Path, *, key: bytes, manifest: Mapping[str, Any]
) -> dict[str, Any]:
    serialized = artifact.read_bytes()
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise BackupError("invalid_backup_manifest")
    if _sha256(serialized) != manifest.get("ciphertext_sha256"):
        raise BackupError("backup_checksum_mismatch")
    try:
        payload = decrypt(key, json.loads(serialized), aad=_AAD)
    except Exception:
        raise BackupError("backup_undecryptable") from None
    destination.mkdir(parents=True, exist_ok=False)
    try:
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "payload.tar"
            archive.write_bytes(payload)
            with tarfile.open(archive) as tar:
                tar.extractall(
                    destination,
                    members=_safe_members(tar, destination),
                    filter="data",
                )
        if _tree_checksum(destination) != manifest.get("content_sha256"):
            raise BackupError("restored_content_mismatch")
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return {"ok": True, "checksum": manifest["content_sha256"]}


def _backup_sources(root: Path) -> list[Path]:
    return [
        root / "config",
        root / "runtime" / "native" / "job_worker.json",
        root / "runtime" / "secret_vault.json",
    ]


def _pg_env(dsn: str, *, database: str | None = None) -> dict[str, str]:
    parsed = urlsplit(dsn)
    if parsed.scheme not in {"postgres", "postgresql"} or not parsed.hostname:
        raise BackupError("invalid_test_database_url")
    source_db = parsed.path.lstrip("/")
    if not source_db or source_db in {"postgres", "template0", "template1"}:
        raise BackupError("unsafe_test_database")
    values = {
        "PGHOST": parsed.hostname,
        "PGPORT": str(parsed.port or 5432),
        "PGDATABASE": database or source_db,
        "PGUSER": parsed.username or "",
    }
    if parsed.password:
        values["PGPASSWORD"] = parsed.password
    return {**os.environ, **values}


def pg_tools_available() -> bool:
    return all(shutil.which(tool) for tool in _TOOLS)


class RealRecoverySteps:
    """Reale Gate-Schritte mit hermetisch injizierbarem Prozess-Runner."""

    def __init__(
        self,
        project_root: str | Path,
        *,
        env: Mapping[str, str] | None = None,
        key: bytes | None = None,
        run: Callable[..., Any] = subprocess.run,
    ) -> None:
        self.root = Path(project_root).resolve()
        self.env = dict(os.environ if env is None else env)
        self.key = key
        self.run = run
        self.work = self.root / "runtime" / "dr_work" / uuid4().hex
        self.state = self.work / "state"
        self.snapshot = self.work / "snapshot"
        self.restore_target = self.work / "restored"
        self.backup: dict[str, Any] = {}
        self.created_databases: list[str] = []

    def _master_key(self) -> bytes:
        if self.key is not None:
            return self.key
        from secondbrain.secret_manager.key_provider import resolve_key_provider

        return resolve_key_provider(self.env).load()

    def snapshot_state(self, project_root: Path) -> dict[str, Any]:
        self.state.mkdir(parents=True)
        for index, source in enumerate(s for s in _backup_sources(self.root) if s.exists()):
            target = self.state / f"artifact-{index}" / source.name
            target.parent.mkdir(parents=True)
            shutil.copytree(source, target) if source.is_dir() else shutil.copy2(source, target)
        shutil.copytree(self.state, self.snapshot)
        return {"ok": True, "checksum": _tree_checksum(self.snapshot)}

    def create_backup(self, project_root: Path) -> dict[str, Any]:
        artifact = self.work / "vault-config.enc"
        manifest = create_encrypted_backup(list(self.state.iterdir()), artifact, key=self._master_key())
        self.backup = {"artifact": artifact, "manifest": manifest}
        return {"ok": True, "checksum": manifest["content_sha256"], **self.backup}

    def validate_checksum(self, backup: dict[str, Any]) -> dict[str, Any]:
        raw = Path(backup["artifact"]).read_bytes()
        return {"ok": _sha256(raw) == backup["manifest"].get("ciphertext_sha256")}

    def mutate_state(self, project_root: Path) -> dict[str, Any]:
        (self.state / "mutation.marker").write_text("mutated", encoding="utf-8")
        return {"ok": True}

    def restore(self, backup: dict[str, Any], project_root: Path) -> dict[str, Any]:
        try:
            restored = restore_encrypted_backup(
                Path(backup["artifact"]),
                self.restore_target,
                key=self._master_key(),
                manifest=backup["manifest"],
            )
            return restored
        except BackupError:
            return {"ok": False}

    def rollback(self, snapshot: dict[str, Any], project_root: Path) -> dict[str, Any]:
        staging = self.work / "rollback.staging"
        shutil.copytree(self.snapshot, staging)
        failed_state = self.work / "failed-state"
        self.state.replace(failed_state)
        staging.replace(self.state)
        shutil.rmtree(failed_state, ignore_errors=True)
        return {"ok": True, "checksum": _tree_checksum(self.state)}

    def failure_checks(self, project_root: Path) -> list[dict[str, Any]]:
        checks: list[dict[str, Any]] = []
        for name, key, manifest in (
            ("wrong_key_restore_blocked", random_key(), self.backup["manifest"]),
            ("tampered_manifest_restore_blocked", self._master_key(), {**self.backup["manifest"], "schema": "invalid"}),
        ):
            target = self.work / name
            try:
                restore_encrypted_backup(self.backup["artifact"], target, key=key, manifest=manifest)
                blocked = False
            except BackupError:
                blocked = True
            checks.append({"name": name, "ok": blocked, "blocking": True})
        return checks

    def _exec(self, args: list[str], env: Mapping[str, str], *, check: bool = True) -> Any:
        return self.run(args, env=dict(env), check=check, capture_output=True, text=True)

    def _database_fingerprints(self, env: Mapping[str, str]) -> dict[str, tuple[int, str]]:
        tables = self._exec(
            ["psql", "-XAt", "-v", "ON_ERROR_STOP=1", "-c",
             "SELECT n.nspname||chr(31)||c.relname FROM pg_class c "
             "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relkind='r' "
             "AND n.nspname NOT IN ('pg_catalog','information_schema') "
             "AND n.nspname NOT LIKE 'pg_toast%' ORDER BY 1"],
            env,
        ).stdout.splitlines()
        result: dict[str, tuple[int, str]] = {}
        for entry in tables:
            schema, table = entry.split("\x1f", 1)
            quoted = f'"{schema.replace(chr(34), chr(34) * 2)}"."{table.replace(chr(34), chr(34) * 2)}"'
            sql = (
                "SELECT count(*)::text||chr(31)||md5(coalesce("
                "string_agg(row_data,'' ORDER BY row_data),'')) FROM "
                f"(SELECT to_jsonb(t)::text AS row_data FROM {quoted} t) q"
            )
            count, checksum = self._exec(
                ["psql", "-XAt", "-v", "ON_ERROR_STOP=1", "-c", sql], env
            ).stdout.strip().split("\x1f", 1)
            result[f"{schema}.{table}"] = (int(count), checksum)
        return result

    def _pgvector_recall(self, env: Mapping[str, str]) -> bool:
        sql = (
            "CREATE TEMP TABLE dr_golden(id int primary key, embedding vector(3));"
            "INSERT INTO dr_golden VALUES (1,'[1,0,0]'),(2,'[0,1,0]'),(3,'[0,0,1]');"
            "SELECT count(*) FROM (VALUES ('[0.99,0.01,0]'::vector,1),"
            "('[0.01,0.99,0]'::vector,2),('[0,0.01,0.99]'::vector,3)) q(v,want) "
            "WHERE (SELECT id FROM dr_golden ORDER BY embedding <=> q.v LIMIT 1)=want"
        )
        return self._exec(
            ["psql", "-XAt", "-v", "ON_ERROR_STOP=1", "-c", sql], env
        ).stdout.strip().splitlines()[-1] == "3"

    def database_checks(self, project_root: Path) -> list[dict[str, Any]]:
        dsn = self.env.get("TEST_DATABASE_URL", "").strip()
        if not dsn:
            return [{"name": "pg_backup_restore", "ok": False,
                     "detail": "SKIP: TEST_DATABASE_URL is not set", "blocking": False}]
        if not pg_tools_available():
            return [{"name": "pg_backup_restore", "ok": False,
                     "detail": "SKIP: PostgreSQL tools unavailable", "blocking": False}]
        try:
            return self._pg_roundtrip(dsn)
        except Exception as exc:
            return [{"name": "pg_backup_restore", "ok": False,
                     "detail": type(exc).__name__, "blocking": True}]

    def _pg_roundtrip(self, dsn: str) -> list[dict[str, Any]]:
        source_env = _pg_env(dsn)
        admin_env = {**source_env, "PGDATABASE": "postgres"}
        restore_db = f"{_DB_PREFIX}restore_{uuid4().hex[:12]}"
        rollback_db = f"{_DB_PREFIX}rollback_{uuid4().hex[:12]}"
        dump = self.work / "database.dump"
        try:
            before = self._database_fingerprints(source_env)
            self._exec(["pg_dump", "--format=custom", "--file", str(dump)], source_env)
            self._exec(["createdb", "--template=template0", restore_db], admin_env)
            self.created_databases.append(restore_db)
            restore_env = {**source_env, "PGDATABASE": restore_db}
            self._exec(["pg_restore", "--no-owner", "--no-privileges", "--single-transaction",
                        "--dbname", restore_db, str(dump)], admin_env)
            after = self._database_fingerprints(restore_env)
            counts_ok = {k: v[0] for k, v in before.items()} == {k: v[0] for k, v in after.items()}
            checksums_ok = before == after
            approval_tables = [
                name for name in before
                if "approval" in name.lower() or name.lower().endswith(".workflow_steps")
            ]
            audit_tables = [
                name for name in before
                if "audit" in name.lower() or name.lower().endswith(".workflow_events")
            ]
            approvals_ok = bool(approval_tables) and all(
                before[name] == after.get(name) for name in approval_tables
            )
            audit_ok = bool(audit_tables) and all(
                before[name] == after.get(name) for name in audit_tables
            )

            self._exec(["createdb", "--template=template0", rollback_db], admin_env)
            self.created_databases.append(rollback_db)
            rollback_env = {**source_env, "PGDATABASE": rollback_db}
            self._exec(["psql", "-X", "-v", "ON_ERROR_STOP=1", "-c",
                        "CREATE TABLE dr_prior_state(id int primary key); INSERT INTO dr_prior_state VALUES (1)"],
                       rollback_env)
            corrupt = self.work / "corrupt.dump"
            corrupt.write_bytes(dump.read_bytes()[: max(1, dump.stat().st_size // 3)])
            failed = self._exec(
                ["pg_restore", "--single-transaction", "--dbname", rollback_db, str(corrupt)],
                admin_env,
                check=False,
            ).returncode != 0
            prior_intact = self._exec(
                ["psql", "-XAt", "-v", "ON_ERROR_STOP=1", "-c",
                 "SELECT count(*) FROM dr_prior_state"], rollback_env
            ).stdout.strip() == "1"
            return [
                {"name": "pg_dump_real", "ok": dump.exists() and dump.stat().st_size > 0},
                {"name": "pg_restore_into_empty_database", "ok": True},
                {"name": "restored_row_counts_match", "ok": counts_ok},
                {"name": "restored_checksums_match", "ok": checksums_ok},
                {"name": "pgvector_golden_recall", "ok": self._pgvector_recall(restore_env)},
                {"name": "approval_integrity", "ok": approvals_ok},
                {"name": "audit_integrity_no_gap", "ok": audit_ok},
                {"name": "failed_restore_blocked", "ok": failed},
                {"name": "failed_restore_atomic_rollback", "ok": failed and prior_intact},
            ]
        finally:
            for database in reversed(self.created_databases):
                self._exec(["dropdb", "--if-exists", "--force", database], admin_env, check=False)
            self.created_databases.clear()

    def cleanup(self) -> None:
        shutil.rmtree(self.work, ignore_errors=True)
