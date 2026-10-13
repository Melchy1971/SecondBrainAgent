"""Live certification for PostgreSQL-backed approval execution and recovery.

Nachgewiesen wird gegen echtes PostgreSQL (nur ``TEST_DATABASE_URL``):

* Transport: ``sslmode=verify-full`` (Zertifikatskette und Hostname).
* Freigaben: approve, reject, expire, deferred -> approved.
* Konkurrierende Entscheidungen: gleichzeitige Reviewer (approve gegen
  reject, gleiche erwartete Version) -- genau eine Entscheidung gewinnt und
  nur sie steht im Audit; doppelte Entscheidung wird nicht doppelt erfasst.
* Persistente Zustandsuebergaenge: jede Pruefung liest ueber eine *neue*
  Verbindung (Neustart-Nachweis); Versionen steigen streng monoton, das Audit
  spiegelt die Reihenfolge; unzulaessige Uebergaenge werden abgewiesen und
  veraendern nichts; Workspace-fremde Entscheidungen greifen nicht.
* Ausfuehrung: genau ein Executor unter Parallelitaet, Replay gesperrt,
  Recovery nach verlorener Lease, abgeloester Executor kann nicht abschliessen.
* Manipulation gespeicherter Payloads bleibt ueber den Binding-Hash erkennbar.

Jedes Objekt liegt in einem eigenen Schema, das im ``finally`` entfernt wird.
Der Report enthaelt weder DSN noch Fehlermeldungen des Treibers.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import threading
from typing import Any, Callable, Iterator, Mapping
from urllib.parse import urlsplit
from uuid import uuid4

PASS, BLOCKED = "PASS", "BLOCKED"
REPORT_PATH = Path("runtime/reports/approval_postgres_live_gate.json")
_PARAM = re.compile(r"(?<!:):([A-Za-z_][A-Za-z0-9_]*)")

WS_A, WS_B = "workspace-a", "workspace-b"
PARALLEL_REVIEWERS = 4
PARALLEL_EXECUTORS = 4


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    check: dict[str, Any] = {"name": name, "ok": bool(ok)}
    if detail:
        check["detail"] = detail
    return check


def _safe_error(exc: BaseException) -> dict[str, str]:
    return {"type": type(exc).__name__, "message": "live database operation failed"}


def _validate_dsn(dsn: str) -> None:
    parsed = urlsplit(dsn)
    if parsed.scheme not in {"postgres", "postgresql", "postgresql+psycopg"} or not parsed.hostname:
        raise ValueError("TEST_DATABASE_URL must be a PostgreSQL DSN")


def _connect(dsn: str):
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("psycopg is required; install requirements-db.txt") from exc
    return psycopg.connect(dsn, connect_timeout=8)


class PsycopgExecutor:
    dialect = "postgresql"

    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def execute(self, statement: str, params: Mapping[str, Any] | None = None) -> list[tuple]:
        with self.connection.cursor() as cursor:
            cursor.execute(_PARAM.sub(r"%(\1)s", statement), dict(params or {}))
            return list(cursor.fetchall()) if cursor.description else []

    @contextmanager
    def transaction(self):
        with self.connection.transaction():
            yield self

    def ping(self) -> bool:
        return self.execute("SELECT 1") == [(1,)]


def _binding(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _binding_intact(item: Mapping[str, Any] | None) -> bool:
    payload = dict((item or {}).get("payload") or {})
    stored = payload.pop("payload_hash", "")
    return bool(stored) and stored == _binding(payload)


def _approval(repo: Any, suffix: str, *, workspace: str = WS_A) -> dict[str, Any]:
    bound = {
        "actor": "gate-actor", "action_type": "connector_write", "connector": "gate",
        "recipient": "test-recipient", "attachments": [], "event_time": "2026-07-17T00:00:00Z",
        "expires_at": "2099-01-01T00:00:00Z", "value": suffix,
    }
    payload = {**bound, "payload_hash": _binding(bound)}
    return repo.create_approval(
        command="connector_write", intent="live certification", text="test data only",
        target="test-recipient", payload=payload, workspace_id=workspace,
        idempotency_key=f"gate-{suffix}-{uuid4().hex}", tool_idempotent=False,
    )


def _decision_events(repo: Any, item_id: str) -> list[str]:
    """Statuswechsel aus dem Audit, ohne Lease-Ereignisse."""
    return [
        str(event.get("new_status"))
        for event in repo.list_audit_events(item_id, workspace_id=WS_A)
        if event.get("new_status") in {"approved", "rejected", "deferred", "expired"}
    ]


class _Live:
    """Verbindungen zum Testschema. ``fresh()`` = neue Session (Neustart-Nachweis)."""

    def __init__(self, dsn: str, schema: str, connect: Callable[[str], Any]) -> None:
        self.dsn, self.schema, self._connect = dsn, schema, connect

    def open(self):
        from psycopg import sql
        from secondbrain.repositories.postgres_review_approval_repository import PostgresReviewApprovalRepository

        connection = self._connect(self.dsn)
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("SET search_path TO {}, public").format(sql.Identifier(self.schema)))
        return connection, PostgresReviewApprovalRepository(PsycopgExecutor(connection))

    @contextmanager
    def fresh(self) -> Iterator[Any]:
        connection, repo = self.open()
        try:
            yield repo
        finally:
            connection.close()

    def read(self, item_id: str) -> dict[str, Any]:
        with self.fresh() as repo:
            return repo.get_item(item_id, workspace_id=WS_A) or {}

    def parallel(self, workers: int, task: Callable[[Any, int], Any]) -> list[Any]:
        """Alle Worker starten gleichzeitig, jeder mit eigener Verbindung.

        Ergebnis je Worker: Rueckgabewert oder der Klassenname einer Ausnahme.
        """
        barrier = threading.Barrier(workers)

        def run(index: int) -> Any:
            # Auch Verbindungsaufbau und Barriere gehoeren in den try: ein
            # langsamer Worker soll als Ursache im Check-Detail erscheinen,
            # nicht das ganze Gate als "live_execution" abbrechen.
            passed = False
            try:
                with self.fresh() as repo:
                    barrier.wait(timeout=30)
                    passed = True
                    return task(repo, index)
            except Exception as exc:  # noqa: BLE001 - nur Klassenname, kein Inhalt
                # Nur wer die Barriere nie erreicht hat, bricht sie ab -- sonst
                # traefe abort() Worker, die gerade noch aus wait() aufwachen.
                if not passed:
                    barrier.abort()
                return type(exc).__name__

        with ThreadPoolExecutor(max_workers=workers) as pool:
            return list(pool.map(run, range(workers)))


def _decision_checks(live: _Live, repo: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    approved = repo.update_status(_approval(repo, "approve")["approval_id"], "approved",
                                  actor="gate-actor", workspace_id=WS_A)
    checks.append(_check("approve", approved is not None and approved["status"] == "approved"))

    restarted = live.read(approved["approval_id"])
    checks.append(_check(
        "restart_persistence",
        restarted.get("status") == "approved" and restarted.get("version") == approved["version"]
        and restarted.get("decided_by") == "gate-actor",
        detail=f"fresh session: status={restarted.get('status')}, version={restarted.get('version')}",
    ))
    checks.append(_check("workspace_isolation", repo.get_item(approved["approval_id"], workspace_id=WS_B) is None))

    rejected = repo.update_status(_approval(repo, "reject")["approval_id"], "rejected",
                                  actor="gate-actor", workspace_id=WS_A)
    checks.append(_check("reject", rejected is not None and rejected["status"] == "rejected"))
    expired = repo.update_status(_approval(repo, "expire")["approval_id"], "expired",
                                 actor="gate-clock", workspace_id=WS_A)
    checks.append(_check("expiration", expired is not None and expired["status"] == "expired"))

    deferred_id = _approval(repo, "defer")["approval_id"]
    repo.update_status(deferred_id, "deferred", actor="gate-actor", workspace_id=WS_A,
                       deferred_until="2099-01-01T00:00:00Z")
    repo.update_status(deferred_id, "approved", actor="gate-actor", workspace_id=WS_A)
    after_defer = live.read(deferred_id)
    with live.fresh() as fresh_repo:
        defer_events = _decision_events(fresh_repo, deferred_id)
    checks.append(_check("deferred_then_approved_persisted",
                         after_defer.get("status") == "approved" and defer_events == ["deferred", "approved"],
                         detail=f"status={after_defer.get('status')}, audit={defer_events}"))

    checks.append(_check("payload_binding", _binding_intact(restarted)))
    return checks, {"approved": approved, "rejected": rejected, "expired": expired}


def _concurrent_decision_checks(live: _Live, repo: Any) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    # -- Reviewer entscheiden gleichzeitig unterschiedlich ---------------------
    contested = _approval(repo, "contested")["approval_id"]
    decisions = ["approved", "rejected"] * (PARALLEL_REVIEWERS // 2)
    outcomes = live.parallel(PARALLEL_REVIEWERS, lambda r, i: r.update_status(
        contested, decisions[i], actor=f"reviewer-{i}", workspace_id=WS_A))
    winners = [decisions[i] for i, outcome in enumerate(outcomes) if isinstance(outcome, dict)]
    losers = sorted({o for o in outcomes if isinstance(o, str)})
    final = live.read(contested)
    with live.fresh() as fresh_repo:
        events = _decision_events(fresh_repo, contested)
    checks.append(_check(
        "concurrent_decisions_single_winner",
        len(winners) == 1 and final.get("status") == winners[0] and events == winners
        and len(final.get("decision_audit") or []) == 1 and set(losers) <= {"ValueError", "RepositoryConflict"},
        detail=f"winners={winners}, losers={losers}, final={final.get('status')}, audit={events}",
    ))

    # -- Optimistische Entscheidung: gleiche erwartete Version ----------------
    optimistic = _approval(repo, "optimistic")
    expected = int(optimistic["version"])
    outcomes = live.parallel(2, lambda r, i: r.update_status(
        optimistic["approval_id"], "approved", actor=f"reviewer-{i}",
        workspace_id=WS_A, expected_version=expected))
    successes = sum(isinstance(o, dict) for o in outcomes)
    final = live.read(optimistic["approval_id"])
    checks.append(_check(
        "concurrent_decisions_with_expected_version",
        successes == 1 and final.get("version") == expected + 1,
        detail=f"successes={successes}, version {expected}->{final.get('version')}, outcomes={[o if isinstance(o, str) else 'ok' for o in outcomes]}",
    ))

    # -- Doppelklick: zweite identische Entscheidung wird nicht erfasst --------
    double = _approval(repo, "double")["approval_id"]
    repo.update_status(double, "approved", actor="gate-actor", workspace_id=WS_A)
    try:
        repo.update_status(double, "approved", actor="gate-actor", workspace_id=WS_A)
        second = "accepted"
    except Exception as exc:  # noqa: BLE001
        second = type(exc).__name__
    with live.fresh() as fresh_repo:
        events = _decision_events(fresh_repo, double)
    checks.append(_check("duplicate_decision_not_recorded_twice",
                         second != "accepted" and events == ["approved"],
                         detail=f"second={second}, audit={events}"))
    return checks


def _invalid_transition_checks(live: _Live, repo: Any, items: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Unzulaessige Uebergaenge scheitern und veraendern weder Status noch Version."""
    checks: list[dict[str, Any]] = []
    attempts = [
        ("rejected_to_approved", items["rejected"], "approved"),
        ("expired_to_approved", items["expired"], "approved"),
        ("approved_to_rejected", items["approved"], "rejected"),
    ]
    for name, item, target in attempts:
        before = live.read(item["approval_id"])
        try:
            repo.update_status(item["approval_id"], target, actor="gate-actor", workspace_id=WS_A)
            outcome = "accepted"
        except Exception as exc:  # noqa: BLE001
            outcome = type(exc).__name__
        after = live.read(item["approval_id"])
        unchanged = (after.get("status"), after.get("version")) == (before.get("status"), before.get("version"))
        checks.append(_check(f"invalid_transition_rejected_{name}", outcome != "accepted" and unchanged,
                             detail=f"outcome={outcome}, status={after.get('status')}, version {before.get('version')}->{after.get('version')}"))

    # Workspace-fremde Entscheidung greift nicht.
    foreign = _approval(repo, "foreign")
    result = repo.update_status(foreign["approval_id"], "approved", actor="intruder", workspace_id=WS_B)
    after = live.read(foreign["approval_id"])
    checks.append(_check("cross_workspace_decision_blocked",
                         result is None and after.get("status") == "pending" and after.get("version") == foreign["version"],
                         detail=f"result={'none' if result is None else 'applied'}, status={after.get('status')}"))
    return checks


def _execution_checks(live: _Live, repo: Any, approved: Mapping[str, Any]) -> list[dict[str, Any]]:
    from secondbrain.repositories.review_approval_repository import RepositoryConflict

    checks: list[dict[str, Any]] = []
    item_id = approved["approval_id"]
    versions = [int(live.read(item_id).get("version", -1))]

    outcomes = live.parallel(PARALLEL_EXECUTORS, lambda r, i: r.acquire_execution_lease(
        item_id, executor_id=f"executor-{i}", workspace_id=WS_A,
        idempotency_key=approved["idempotency_key"]))
    granted = sum(isinstance(o, dict) for o in outcomes)
    checks.append(_check("parallel_exactly_once", granted == 1,
                         detail=f"granted={granted}/{PARALLEL_EXECUTORS}, others={sorted({o for o in outcomes if isinstance(o, str)})}"))
    executing = live.read(item_id)
    versions.append(int(executing.get("version", -1)))

    completed = repo.release_execution_lease(item_id, execution_token=str(executing.get("execution_token")),
                                             workspace_id=WS_A, result={"test": True})
    final = live.read(item_id)
    versions.append(int(final.get("version", -1)))
    checks.append(_check("execution_audit", completed["status"] == "completed"
                         and len(repo.list_audit_events(item_id, workspace_id=WS_A)) >= 3))

    with live.fresh() as fresh_repo:
        path = [str(e.get("new_status")) for e in fresh_repo.list_audit_events(item_id, workspace_id=WS_A)]
    checks.append(_check(
        "lifecycle_transitions_persisted",
        final.get("status") == "completed" and versions == sorted(set(versions)) and len(set(versions)) == 3
        and path[-3:] == ["approved", "executing", "completed"],
        detail=f"fresh session: status={final.get('status')}, versions={versions}, audit={path}",
    ))

    try:
        repo.acquire_execution_lease(item_id, executor_id="replay", workspace_id=WS_A)
        replay_blocked = False
    except RepositoryConflict:
        replay_blocked = True
    checks.append(_check("replay_blocked", replay_blocked))

    before = live.read(item_id)
    try:
        repo.update_status(item_id, "approved", actor="gate-actor", workspace_id=WS_A)
        outcome = "accepted"
    except Exception as exc:  # noqa: BLE001
        outcome = type(exc).__name__
    after = live.read(item_id)
    checks.append(_check("invalid_transition_rejected_completed_to_approved",
                         outcome != "accepted" and after.get("version") == before.get("version")
                         and after.get("status") == "completed",
                         detail=f"outcome={outcome}, status={after.get('status')}"))
    return checks


def _recovery_checks(live: _Live, repo: Any) -> list[dict[str, Any]]:
    """Executor faellt aus: Uebergang in recovery_required, Wiederaufnahme, Abschluss."""
    from secondbrain.repositories.review_approval_repository import RepositoryConflict

    checks: list[dict[str, Any]] = []
    item = _approval(repo, "recovery")
    item_id = item["approval_id"]
    repo.update_status(item_id, "approved", actor="gate-actor", workspace_id=WS_A)
    crashed = repo.acquire_execution_lease(item_id, executor_id="executor-crashed", workspace_id=WS_A)
    repo.update_status(item_id, "recovery_required", actor="gate-recovery", workspace_id=WS_A,
                       note="lease lost")
    after_crash = live.read(item_id)

    with live.fresh() as fresh_repo:
        resumed = fresh_repo.acquire_execution_lease(item_id, executor_id="executor-recovery", workspace_id=WS_A)
    try:
        repo.release_execution_lease(item_id, execution_token=str(crashed["execution_token"]), workspace_id=WS_A)
        stale = "accepted"
    except RepositoryConflict:
        stale = "rejected"
    checks.append(_check("stale_executor_cannot_complete_after_recovery", stale == "rejected",
                         detail=f"old token {stale}"))

    repo.release_execution_lease(item_id, execution_token=str(resumed["execution_token"]),
                                 workspace_id=WS_A, result={"recovered": True})
    final = live.read(item_id)
    checks.append(_check(
        "recovery_after_lost_lease",
        after_crash.get("status") == "recovery_required" and final.get("status") == "completed"
        and _binding_intact(final),
        detail=f"after crash={after_crash.get('status')}, final={final.get('status')}",
    ))
    return checks


def _tamper_checks(live: _Live, repo: Any) -> list[dict[str, Any]]:
    """Direkter Schreibzugriff auf die gespeicherte Payload bleibt erkennbar."""
    item = _approval(repo, "tamper")
    intact_before = _binding_intact(live.read(item["approval_id"]))
    connection, _ = live.open()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT data FROM review_approval_items WHERE id = %s", (item["approval_id"],))
            data = json.loads(cursor.fetchone()[0])
            data["payload"]["recipient"] = "attacker@example.invalid"
            cursor.execute("UPDATE review_approval_items SET data = %s WHERE id = %s",
                           (json.dumps(data, ensure_ascii=False), item["approval_id"]))
    finally:
        connection.close()
    intact_after = _binding_intact(live.read(item["approval_id"]))
    return [_check("persisted_payload_tamper_detectable", intact_before and not intact_after,
                   detail=f"binding before={intact_before}, after tamper={intact_after}")]


def _run_live(dsn: str, schema: str, connect: Callable[[str], Any]) -> tuple[list[dict[str, Any]], bool]:
    from psycopg import sql
    from secondbrain.release.postgres_live_gate import effective_sslmode

    checks: list[dict[str, Any]] = []
    live = _Live(dsn, schema, connect)
    conn = connect(dsn)
    conn.autocommit = True
    created = False
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT current_setting('server_version_num')::int")
            checks.append(_check("postgresql", cursor.fetchone()[0] >= 140000))
        sslmode = effective_sslmode(conn, dsn)
        checks.append(_check("tls_verify_full", sslmode == "verify-full", detail=f"sslmode={sslmode}"))
        with conn.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            created = True

        setup_conn, repo = live.open()
        try:
            repo.ensure_schema()
            checks += [_check("postgres_repository", repo.health().healthy),
                       _check("no_development_fallback", repo.backend == "postgres")]
            decision_checks, items = _decision_checks(live, repo)
            checks += decision_checks
            checks += _concurrent_decision_checks(live, repo)
            checks += _invalid_transition_checks(live, repo, items)
            checks += _execution_checks(live, repo, items["approved"])
            checks += _recovery_checks(live, repo)
            checks += _tamper_checks(live, repo)
        finally:
            setup_conn.close()
    finally:
        cleanup = not created
        if created:
            try:
                with conn.cursor() as cursor:
                    cursor.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))
                cleanup = True
            except Exception:  # noqa: BLE001
                cleanup = False
        conn.close()
    return checks, cleanup


def run_approval_postgres_live_gate(
    project_root: str | Path = ".", *, env: Mapping[str, str] | None = None,
    connect: Callable[[str], Any] | None = None, write_report: bool = True,
) -> dict[str, Any]:
    source = os.environ if env is None else env
    dsn = str(source.get("TEST_DATABASE_URL") or "")
    schema = f"sb_approval_gate_{uuid4().hex[:12]}"
    checks: list[dict[str, Any]] = []
    cleanup = False
    if not dsn:
        checks.append(_check("test_database_url", False))
    else:
        try:
            _validate_dsn(dsn)
            checks.append(_check("test_database_url", True))
            live, cleanup = _run_live(dsn, schema, connect or _connect)
            checks.extend(live)
        except Exception as exc:  # noqa: BLE001
            checks.append({**_check("live_execution", False), "error": _safe_error(exc)})
    failed = [check["name"] for check in checks if not check["ok"]]
    report = {
        "schema": "secondbrain.approval_postgres_live_gate.v1", "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": PASS if not failed else BLOCKED, "ok": not failed,
        "backend": "postgresql" if dsn else "not_configured", "test_data_only": True,
        "checks": checks, "failed_checks": failed, "evidence": {"test_schema": schema, "cleanup": cleanup},
    }
    from secondbrain.release.evidence import seal

    report = seal(report, schema=report["schema"], root=project_root, env=source)
    if write_report:
        target = Path(project_root).resolve() / REPORT_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report["report"] = REPORT_PATH.as_posix()
    return report
