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
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

from secondbrain.secret_manager.crypto import decrypt, encrypt, random_key
from secondbrain.storage import vector_index

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
        if not (member.isfile() or member.isdir()):
            raise BackupError("backup_special_files_forbidden")  # Geraete, FIFOs
    return members


def _extract(tar: tarfile.TarFile, destination: Path) -> None:
    """Entpackt nach Pruefung durch ``_safe_members``.

    ``filter="data"`` gibt es erst ab Python 3.11.4 / 3.12; das Projekt
    unterstuetzt ``>=3.11``. Ohne den Parameter bleibt ``_safe_members`` die
    Schutzschicht (Pfadausbruch, Links, Sonderdateien).
    """
    members = _safe_members(tar, destination)
    if hasattr(tarfile, "data_filter"):
        tar.extractall(destination, members=members, filter="data")
    else:  # pragma: no cover - nur Python < 3.11.4
        tar.extractall(destination, members=members)


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
                _extract(tar, destination)
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
    # TLS-Parameter des DSN an die libpq-Werkzeuge weiterreichen. Ohne sie
    # verbaenden sich pg_dump/pg_restore mit sslmode=prefer -- verschluesselt,
    # aber ohne Pruefung von Zertifikatskette und Hostname.
    query = parse_qs(parsed.query)
    for param, variable in _TLS_PARAMS:
        if query.get(param):
            values[variable] = query[param][-1]
    return {**os.environ, **values}


_TLS_PARAMS = (
    ("sslmode", "PGSSLMODE"), ("sslrootcert", "PGSSLROOTCERT"),
    ("sslcert", "PGSSLCERT"), ("sslkey", "PGSSLKEY"), ("sslcrl", "PGSSLCRL"),
)


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

    def _psql(self, env: Mapping[str, str], sql: str) -> str:
        return self._exec(["psql", "-XAt", "-v", "ON_ERROR_STOP=1", "-c", sql], env).stdout.strip()

    def _seed_fixture(self, env: Mapping[str, str], schema: str) -> None:
        """Deterministische Testdaten: Approvals, lueckenloses Audit, Vektoren mit HNSW."""
        self._exec(["psql", "-X", "-q", "-v", "ON_ERROR_STOP=1", "-c", _fixture_sql(schema)], env)

    def _restored_vector_recall(self, env: Mapping[str, str], schema: str) -> tuple[int, int, bool]:
        """Jeder gespeicherte Vektor muss sich selbst als naechsten Nachbarn finden.

        Liefert zusaetzlich, ob der Plan den wiederhergestellten HNSW-Index
        tatsaechlich nutzt -- ``enable_seqscan = off`` schreckt den Planner nur
        ab, erzwingt den Index aber nicht.
        """
        distance = vector_index.distance_expression(
            dimensions=_FIXTURE_DIMENSIONS, column="w.embedding", parameter="v.embedding")
        query = (f"SELECT count(*) FROM {schema}.dr_vectors v WHERE v.id = ("
                 f"SELECT w.id FROM {schema}.dr_vectors w ORDER BY {distance} LIMIT 1)")
        hits = self._psql(env, f"SET enable_seqscan = off; {query}").splitlines()[-1]
        plan = self._psql(env, f"SET enable_seqscan = off; EXPLAIN {query}")
        return int(hits), _FIXTURE_VECTORS, "Index Scan using dr_vectors_hnsw" in plan

    def database_checks(self, project_root: Path) -> list[dict[str, Any]]:
        dsn = self.env.get("TEST_DATABASE_URL", "").strip()
        if not dsn:
            return [{"name": "pg_backup_restore", "ok": False,
                     "detail": "SKIP: TEST_DATABASE_URL is not set", "blocking": False}]
        if not pg_tools_available():
            return [{"name": "pg_backup_restore", "ok": False,
                     "detail": "SKIP: PostgreSQL tools unavailable", "blocking": False}]
        sslmode = (_pg_env(dsn).get("PGSSLMODE") or "prefer").lower()
        if sslmode != "verify-full":
            # Dumps enthalten saemtliche Daten; ein Transport ohne Zertifikats-
            # und Hostnamenpruefung ist hier genauso unzulaessig wie im Live-Gate.
            return [{"name": "pg_tls_verify_full", "ok": False,
                     "detail": f"sslmode={sslmode}; verify-full required", "blocking": True}]
        try:
            return [{"name": "pg_tls_verify_full", "ok": True, "detail": "sslmode=verify-full"},
                    *self._pg_roundtrip(dsn)]
        except Exception as exc:
            return [{"name": "pg_backup_restore", "ok": False,
                     "detail": _diagnose(exc), "blocking": True}]

    def _restore_template(self) -> str:
        template = (self.env.get("DR_RESTORE_TEMPLATE") or "template0").strip()
        if not template.replace("_", "").isalnum():
            raise BackupError("invalid_restore_template")
        return template

    def _create_target(self, name: str, admin_env: Mapping[str, str],
                       source_env: Mapping[str, str]) -> dict[str, str]:
        """Leeres Restore-Ziel. Ein vom Administrator bereitgestelltes Template
        (``DR_RESTORE_TEMPLATE``) darf nur Extensions enthalten -- nicht
        vertrauenswuerdige wie pgvector kann eine Rolle ohne Superuser-Recht
        sonst nicht anlegen."""
        self._exec(["createdb", f"--template={self._restore_template()}", name], admin_env)
        self.created_databases.append(name)
        return {**source_env, "PGDATABASE": name}

    def _restore_args(self, archive: Path, database: str, target_env: Mapping[str, str],
                      admin_env: Mapping[str, str]) -> list[str]:
        """Atomarer Restore; im Ziel bereits vorhandene Extensions werden
        uebersprungen (CREATE/COMMENT ON EXTENSION erfordern Eigentuemerrechte)."""
        args = ["--no-owner", "--no-privileges", "--single-transaction", "--exit-on-error",
                "--dbname", database]
        present = set(self._psql(target_env, "SELECT extname FROM pg_extension").split())
        listing = self._exec(["pg_restore", "--list", str(archive)], admin_env).stdout
        filtered, skipped = _skip_present_extensions(listing, present)
        if skipped:
            list_file = self.work / f"{database}.list"
            list_file.write_text(filtered, encoding="utf-8")
            args += ["--use-list", str(list_file)]
        return args

    def _pg_roundtrip(self, dsn: str) -> list[dict[str, Any]]:
        source_env = _pg_env(dsn)
        admin_env = {**source_env, "PGDATABASE": "postgres"}
        fixture = f"{_DB_PREFIX}fx_{uuid4().hex[:10]}"
        restore_db = f"{_DB_PREFIX}restore_{uuid4().hex[:12]}"
        rollback_db = f"{_DB_PREFIX}rollback_{uuid4().hex[:12]}"
        dump = self.work / "database.dump"
        directory_dump = self.work / "database.dir"
        self.work.mkdir(parents=True, exist_ok=True)
        seeded = False
        try:
            self._seed_fixture(source_env, fixture)
            seeded = True
            before = self._database_fingerprints(source_env)

            # -- Echter pg_dump (Custom-Format) und Restore in leere Datenbank ----
            self._exec(["pg_dump", "--format=custom", "--file", str(dump)], source_env)
            restore_env = self._create_target(restore_db, admin_env, source_env)
            empty_before = self._database_fingerprints(restore_env) == {}
            self._exec(["pg_restore", *self._restore_args(dump, restore_db, restore_env, admin_env),
                        str(dump)], admin_env)
            after = self._database_fingerprints(restore_env)

            counts_ok = {k: v[0] for k, v in before.items()} == {k: v[0] for k, v in after.items()}
            checksums_ok = before == after
            approvals = f"{fixture}.dr_approvals"
            audit = f"{fixture}.dr_audit"
            hash_mismatches = int(self._psql(restore_env, (
                f"SELECT count(*) FROM {approvals} WHERE payload_hash <> "
                "encode(sha256(convert_to(payload::text, 'UTF8')), 'hex')")))
            approvals_ok = (approvals in after and before.get(approvals) == after.get(approvals)
                            and after[approvals][0] == _FIXTURE_APPROVALS and hash_mismatches == 0)
            audit_gapless = self._psql(restore_env, (
                f"SELECT count(*) = max(seq) AND min(seq) = 1 FROM {audit}")) == "t"
            audit_ok = (audit in after and before.get(audit) == after.get(audit)
                        and after[audit][0] == _FIXTURE_AUDIT and audit_gapless)
            recall_hits, recall_total, index_used = self._restored_vector_recall(restore_env, fixture)

            # -- Restore-Fehler mitten im Lauf: alles muss zurueckgerollt werden --
            self._exec(["pg_dump", "--format=directory", "--compress=0", "--file",
                        str(directory_dump)], source_env)
            listing = self._exec(["pg_restore", "--list", str(directory_dump)], admin_env).stdout
            corrupted_table = _corrupt_last_table_data(directory_dump, listing, fixture)
            rollback_env = self._create_target(rollback_db, admin_env, source_env)
            self._psql(rollback_env, "CREATE TABLE dr_prior_state(id int primary key); "
                                     "INSERT INTO dr_prior_state VALUES (1)")
            prior_before = self._database_fingerprints(rollback_env)
            failed_run = self._exec(
                ["pg_restore", *self._restore_args(directory_dump, rollback_db, rollback_env, admin_env),
                 "--verbose", str(directory_dump)],
                admin_env, check=False,
            )
            progress = _restore_progress(failed_run.stderr or "")
            failed = failed_run.returncode != 0
            leftover_schema = self._psql(rollback_env, (
                f"SELECT count(*) FROM pg_namespace WHERE nspname = '{fixture}'")) != "0"
            prior_after = self._database_fingerprints(rollback_env)
            rolled_back = failed and not leftover_schema and prior_after == prior_before

            return [
                {"name": "pg_dump_real", "ok": dump.exists() and dump.stat().st_size > 0,
                 "detail": f"{dump.stat().st_size if dump.exists() else 0} bytes, custom format"},
                {"name": "restore_target_empty_before_restore", "ok": empty_before},
                {"name": "pg_restore_into_empty_database",
                 "ok": empty_before and bool(after) and set(after) == set(before),
                 "detail": f"{len(after)} tables restored, {len(before)} in source"},
                {"name": "restored_row_counts_match", "ok": counts_ok},
                {"name": "restored_checksums_match", "ok": checksums_ok},
                {"name": "pgvector_golden_recall", "ok": recall_hits == recall_total and index_used,
                 "detail": (f"{recall_hits}/{recall_total} restored vectors, "
                            f"restored HNSW index used={index_used}")},
                {"name": "approval_integrity", "ok": approvals_ok,
                 "detail": f"rows={after.get(approvals, (0,))[0]}, hash mismatches={hash_mismatches}"},
                {"name": "audit_integrity_no_gap", "ok": audit_ok,
                 "detail": f"rows={after.get(audit, (0,))[0]}, gapless={audit_gapless}"},
                {"name": "failed_restore_blocked", "ok": failed,
                 "detail": f"pg_restore exit={failed_run.returncode}, corrupted={corrupted_table}"},
                {"name": "failed_restore_mid_restore",
                 "ok": failed and progress["completed_data"] >= 1 and progress["created_tables"] >= 1,
                 "detail": (f"before failure: {progress['created_tables']} tables created, "
                            f"{progress['completed_data']} table data loaded")},
                {"name": "failed_restore_atomic_rollback", "ok": rolled_back,
                 "detail": (f"leftover objects={leftover_schema}, "
                            f"prior state intact={prior_after == prior_before}")},
            ]
        finally:
            for database in reversed(self.created_databases):
                self._exec(["dropdb", "--if-exists", "--force", database], admin_env, check=False)
            self.created_databases.clear()
            if seeded:
                self._exec(["psql", "-X", "-q", "-c", f"DROP SCHEMA IF EXISTS {fixture} CASCADE"],
                           source_env, check=False)

    def cleanup(self) -> None:
        shutil.rmtree(self.work, ignore_errors=True)


# --------------------------------------------------------------------------
# Testdaten und Fehlerinjektion fuer den PostgreSQL-Roundtrip
# --------------------------------------------------------------------------

_FIXTURE_APPROVALS = 25
_FIXTURE_AUDIT = 50
_FIXTURE_VECTORS = 30
# Projektdimension: Der Restore muss den produktiven halfvec-Index-Pfad tragen.
_FIXTURE_DIMENSIONS = vector_index.DEFAULT_DIMENSIONS


def _fixture_sql(schema: str) -> str:
    """Approvals mit Payload-Hash, lueckenloses Audit (2 Ereignisse je Approval)
    und deterministische Vektoren mit HNSW-Index. Alles im eigenen Schema."""
    if not schema.replace("_", "").isalnum():
        raise BackupError("invalid_fixture_schema")
    return (
        f"CREATE SCHEMA {schema};"
        f"CREATE TABLE {schema}.dr_approvals (id text PRIMARY KEY, status text NOT NULL,"
        " version int NOT NULL, payload jsonb NOT NULL, payload_hash text NOT NULL);"
        f"CREATE TABLE {schema}.dr_audit (seq bigserial PRIMARY KEY,"
        f" item_id text NOT NULL REFERENCES {schema}.dr_approvals(id), event jsonb NOT NULL);"
        f"CREATE TABLE {schema}.dr_vectors (id int PRIMARY KEY,"
        f" embedding vector({_FIXTURE_DIMENSIONS}) NOT NULL);"
        f"INSERT INTO {schema}.dr_approvals (id, status, version, payload, payload_hash)"
        " SELECT 'appr-' || g, (ARRAY['pending','approved','rejected','completed','expired'])[1 + g % 5],"
        " g % 4, p, encode(sha256(convert_to(p::text, 'UTF8')), 'hex')"
        f" FROM generate_series(1, {_FIXTURE_APPROVALS}) g,"
        " LATERAL (SELECT jsonb_build_object('recipient', 'r' || g, 'value', g, 'note', 'Grüße ' || g)) x(p);"
        f"INSERT INTO {schema}.dr_audit (item_id, event)"
        " SELECT 'appr-' || g, jsonb_build_object('step', s, 'new_status', 'approved')"
        f" FROM generate_series(1, {_FIXTURE_APPROVALS}) g, generate_series(1, 2) s ORDER BY g, s;"
        f"INSERT INTO {schema}.dr_vectors (id, embedding)"
        " SELECT g, (SELECT array_agg(cos(g * k * 0.001)::real ORDER BY k)"
        f" FROM generate_series(1, {_FIXTURE_DIMENSIONS}) k)::vector"
        f" FROM generate_series(1, {_FIXTURE_VECTORS}) g;"
        + vector_index.hnsw_index_sql(table=f"{schema}.dr_vectors", dimensions=_FIXTURE_DIMENSIONS,
                                      name="dr_vectors_hnsw") + ";"
    )


def _corrupt_last_table_data(directory: Path, listing: str, schema: str) -> str:
    """Macht den Datenblock der zuletzt geladenen Testtabelle unlesbar.

    Im Verzeichnisformat (unkomprimiert) liegt jede Tabelle als ``<id>.dat``
    im COPY-Textformat vor. Eine Zeile mit falscher Spaltenzahl vor dem
    Endemarker laesst COPY scheitern -- erst nachdem Schema, Tabellen und die
    Daten frueherer Tabellen bereits verarbeitet wurden.
    """
    entries = []
    for line in listing.splitlines():
        line = line.strip()
        if not line or line.startswith(";") or " TABLE DATA " not in line:
            continue
        dump_id = line.split(";", 1)[0].strip()
        if f" {schema} " in f" {line} ":
            entries.append((dump_id, line))
    if len(entries) < 2:
        raise BackupError("fixture_table_data_missing")
    dump_id, line = entries[-1]
    data_file = directory / f"{dump_id}.dat"
    raw = data_file.read_text(encoding="utf-8")
    marker = "\\.\n"
    if marker not in raw:
        raise BackupError("unexpected_copy_format")
    data_file.write_text(raw.replace(marker, "corrupt-row-without-columns\n" + marker, 1),
                         encoding="utf-8", newline="\n")
    return line.split(" TABLE DATA ", 1)[1].split()[1]


def _restore_progress(verbose_log: str) -> dict[str, int]:
    """Zaehlt, was pg_restore --verbose vor dem Abbruch bereits verarbeitet hat."""
    created = processed = 0
    for line in verbose_log.splitlines():
        if "creating TABLE " in line:
            created += 1
        elif "processing data for table " in line:
            processed += 1
    # Der letzte "processing data"-Eintrag ist der scheiternde Block.
    return {"created_tables": created, "completed_data": max(0, processed - 1)}


def _skip_present_extensions(listing: str, present: set[str]) -> tuple[str, list[str]]:
    """Kommentiert EXTENSION- und COMMENT-ON-EXTENSION-Eintraege fuer bereits
    vorhandene Extensions im pg_restore-Inhaltsverzeichnis aus."""
    skipped: list[str] = []
    lines = []
    for line in listing.splitlines():
        hit = next((ext for ext in present
                    if f" EXTENSION - {ext} " in f"{line} " or f" COMMENT - EXTENSION {ext} " in f"{line} "), None)
        if hit and not line.lstrip().startswith(";"):
            skipped.append(hit)
            line = ";" + line
        lines.append(line)
    return "\n".join(lines) + "\n", skipped


_KNOWN_FAILURES = (
    ("permission denied to create extension",
     "restore target lacks a required extension; provision DR_RESTORE_TEMPLATE with it"),
    ("permission denied to create database", "role needs CREATEDB for restore targets"),
)


def _diagnose(exc: BaseException) -> str:
    """Fehlerklasse plus feste Handlungshilfe fuer bekannte Ursachen.

    Die Werkzeugausgabe selbst wird nie uebernommen -- sie kann Hostnamen
    oder Datenbanknamen enthalten.
    """
    stderr = str(getattr(exc, "stderr", "") or "")
    for marker, hint in _KNOWN_FAILURES:
        if marker in stderr:
            return f"{type(exc).__name__}: {hint}"
    return type(exc).__name__
