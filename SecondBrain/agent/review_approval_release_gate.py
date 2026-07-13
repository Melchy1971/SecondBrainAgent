"""Final security and release gate for the review/approval governance layer.

Aggregates the end-to-end approval gate with dedicated checks for every layer
built on top of it: memory-write governance, notifications/escalation, metrics,
concurrency, crash recovery and repository health. Produces a single verdict
(PASS / CONDITIONAL_PASS / BLOCKED) plus a machine-readable report.

Every check is defensive: a check helper that raises is recorded as a failing
check rather than crashing the gate, so the gate always returns a controlled
verdict.
"""

from __future__ import annotations

import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

from secondbrain.agent.review_approval_gate import (
    BLOCKED,
    CONDITIONAL_PASS,
    PASS,
    GateCheck,
    evaluate_gate_status,
    run_review_approval_gate,
)

RELEASE_VERSION = "v30.86"
SCHEMA = "secondbrain.review_approval_release_gate.v1"

TEST_COMMANDS = [
    "pytest -q tests/test_review_approval_release_gate.py",
    "pytest -q tests/test_review_approval_e2e.py",
    "pytest -q tests/test_review_approval_security.py",
    "pytest -q tests/test_review_approval_concurrency.py",
    "pytest -q",
]

_SECURITY_CHECK_IDS = {
    "delete_requires_approval",
    "send_requires_approval",
    "external_write_requires_approval",
    "sensitive_payload_redacted",
    "decision_audit",
    "memory_sensitive_blocked",
    "memory_privacy_mode_blocked",
    "memory_no_secret_leak",
    "metrics_no_secret_leak",
    "workspace_isolation",
    "parallel_decision_conflict_safe",
    "no_double_execution",
    "credential_change_requires_approval",
    "scope_change_requires_approval",
    "confirmed_boolean_blocked",
    "connector_payload_bound",
    "connector_workspace_bound",
    "connector_expiration_enforced",
    "connector_single_use",
    "gui_no_secret_leak",
    "production_backend",
    "postgresql_health",
}

_CHECK_GROUPS = {
    "data_model": {
        "review_item_model", "approval_item_model", "status_transitions",
        "optimistic_versioning", "workspace_isolation",
    },
    "agent": {
        "low_risk_direct", "risky_tool_pauses", "approval_persisted",
        "approve_exactly_once", "reject_prevents_execution", "defer_holds_plan",
        "restart_retains_pending",
    },
    "security": {
        "delete_requires_approval", "send_requires_approval",
        "external_write_requires_approval", "credential_change_requires_approval",
        "scope_change_requires_approval", "memory_privacy_mode_blocked",
        "sensitive_payload_redacted", "confirmed_boolean_blocked",
    },
    "import": {
        "import_failed_review", "import_sensitive_review",
        "import_low_confidence_review", "import_approve_resumes",
        "import_reject_stops", "import_defer_pauses", "import_no_duplicates",
    },
    "memory": {
        "memory_sensitive_blocked", "memory_low_confidence_review",
        "memory_privacy_mode_blocked", "memory_no_secret_leak",
        "memory_approve_once", "memory_evidence_present",
    },
    "connector": {
        "connector_scope_diff_bound", "connector_payload_bound",
        "connector_workspace_bound", "connector_expiration_enforced",
        "connector_single_use",
    },
    "operations": {
        "decision_audit", "notifications_risky_alert", "notifications_escalation",
        "metrics_no_secret_leak", "metrics_computable", "no_double_execution",
        "parallel_decision_conflict_safe", "crash_recovery_status",
        "corrupt_queue_recoverable", "repository_health", "production_backend",
        "postgresql_health",
    },
    "gui": {
        "viewmodel_visible", "gui_inbox_reachable", "gui_badge_correct",
        "gui_decisions", "gui_error_state", "gui_no_secret_leak",
        "gui_no_technical_ids", "corrupt_queue_controlled",
    },
}


def _check_group(check_id: str) -> str:
    for group, check_ids in _CHECK_GROUPS.items():
        if check_id in check_ids:
            return group
    return "operations"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _guard(check_id: str, title: str, fn: Callable[[], GateCheck], *, hard_blocker: bool) -> GateCheck:
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - a broken check must not crash the gate
        return GateCheck(check_id, title, False, f"check_error:{type(exc).__name__}:{exc}", hard_blocker=hard_blocker)


class ReviewApprovalReleaseGate:
    def __init__(
        self,
        project_root: str | Path = ".",
        *,
        env: Mapping[str, str] | None = None,
        repository_executor: Any | None = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.env = env
        self.repository_executor = repository_executor
        self.backend_status: dict[str, Any] = {}
        self.metrics: dict[str, Any] = {}

    def run(self, *, write_report: bool = True) -> dict[str, Any]:
        checks: list[GateCheck] = []
        checks.extend(self._foundation_checks())
        with tempfile.TemporaryDirectory(prefix="secondbrain-release-gate-") as directory:
            root = Path(directory)
            checks.extend(self._data_model_checks(root))
            checks.extend(self._import_checks(root))
            checks.extend(self._memory_checks(root))
            checks.extend(self._connector_checks(root))
            checks.extend(self._notification_checks(root))
            checks.extend(self._metrics_checks(root))
            checks.extend(self._concurrency_checks(root))
            checks.extend(self._recovery_checks(root))
            checks.extend(self._repository_checks(root))
            checks.extend(self._gui_checks(root))
            self.metrics = self._collect_metrics(root)

        overall = evaluate_gate_status(checks)
        check_dicts = [
            {**check.to_dict(), "group": _check_group(check.check_id)}
            for check in checks
        ]
        blockers = [c["check_id"] for c in check_dicts if c["status"] == BLOCKED]
        warnings = [c["check_id"] for c in check_dicts if c["status"] == CONDITIONAL_PASS]
        report = {
            "schema": SCHEMA,
            "version": RELEASE_VERSION,
            "timestamp": _utc_now(),
            "overall_status": overall,
            "ok": overall != BLOCKED,
            "summary": {
                "total": len(check_dicts),
                "passed": sum(1 for c in check_dicts if c["status"] == PASS),
                "conditional": len(warnings),
                "blocked": len(blockers),
            },
            "checks": check_dicts,
            "blockers": blockers,
            "warnings": warnings,
            "metrics": self.metrics,
            "test_commands": TEST_COMMANDS,
            "backend_status": self.backend_status,
            "security_summary": {
                c["check_id"]: c["status"]
                for c in check_dicts
                if c["check_id"] in _SECURITY_CHECK_IDS
            },
            "release_recommendation": {
                PASS: "RELEASE",
                CONDITIONAL_PASS: "RELEASE_WITH_NONCRITICAL_WARNINGS",
                BLOCKED: "DO_NOT_RELEASE",
            }[overall],
        }
        if write_report:
            self._write_report(report)
        return report

    def _write_report(self, report: dict[str, Any]) -> None:
        path = self.project_root / "runtime" / "reports" / "review_approval_release_gate.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)

    # -- data model -------------------------------------------------------

    def _data_model_checks(self, root: Path) -> list[GateCheck]:
        from secondbrain.native.approval import APPROVAL_SCHEMA, REVIEW_SCHEMA
        from secondbrain.repositories.jsonl_review_approval_repository import (
            JsonlReviewApprovalRepository,
        )
        from secondbrain.repositories.postgres_review_approval_repository import (
            PostgresReviewApprovalRepository,
        )
        from secondbrain.repositories.review_approval_repository import RepositoryConflict
        from secondbrain.storage.db_executor import SqliteExecutor

        repository = JsonlReviewApprovalRepository(root / "model")
        approval = repository.create_approval(
            command="records.delete",
            intent="delete",
            text="Delete",
            category="delete_request",
            risk_level="high",
            workspace_id="workspace-a",
        )
        review = repository.create_review(
            category="sensitive_document",
            title="Sensitive document",
            metadata={"workspace_id": "workspace-a"},
        )

        def approval_model() -> GateCheck:
            required = {
                "approval_id", "status", "version", "workspace_id",
                "idempotency_key", "decision_audit",
            }
            ok = approval.get("schema") == APPROVAL_SCHEMA and required.issubset(approval)
            return GateCheck(
                "approval_item_model", "ApprovalItem production fields are present",
                ok, f"required_fields={len(required)}", hard_blocker=True,
            )

        def review_model() -> GateCheck:
            required = {"review_id", "status", "category", "metadata", "decision_audit"}
            ok = review.get("schema") == REVIEW_SCHEMA and required.issubset(review)
            return GateCheck(
                "review_item_model", "ReviewItem production fields are present",
                ok, f"required_fields={len(required)}", hard_blocker=True,
            )

        def transitions() -> GateCheck:
            deferred = repository.compare_and_set_status(
                approval["approval_id"], 0, "deferred", actor="gate"
            )
            approved = repository.compare_and_set_status(
                approval["approval_id"], deferred["version"], "approved", actor="gate"
            )
            rejected_review = repository.compare_and_set_status(
                review["review_id"], 0, "rejected", actor="gate"
            )
            ok = approved["status"] == "approved" and rejected_review["status"] == "rejected"
            return GateCheck(
                "status_transitions", "Review and approval transitions are validated",
                ok, "deferred->approved; pending->rejected", hard_blocker=True,
            )

        def versioning() -> GateCheck:
            stale_rejected = False
            try:
                repository.compare_and_set_status(
                    approval["approval_id"], 0, "rejected", actor="stale"
                )
            except RepositoryConflict:
                stale_rejected = True
            current = repository.get_item(approval["approval_id"]) or {}
            ok = stale_rejected and int(current.get("version") or 0) == 2
            return GateCheck(
                "optimistic_versioning", "Stale item versions are rejected",
                ok, f"version={current.get('version')}", hard_blocker=True,
            )

        def workspace_isolation() -> GateCheck:
            pg = PostgresReviewApprovalRepository(SqliteExecutor(":memory:"))
            pg.ensure_schema()
            first = pg.create_approval(
                command="records.delete", intent="delete", text="A",
                category="delete_request", risk_level="high", workspace_id="w1",
            )
            pg.create_approval(
                command="records.delete", intent="delete", text="B",
                category="delete_request", risk_level="high", workspace_id="w2",
            )
            ok = (
                len(pg.list_items(workspace_id="w1")) == 1
                and len(pg.list_items(workspace_id="w2")) == 1
                and pg.get_item(first["approval_id"], workspace_id="w2") is None
            )
            return GateCheck(
                "workspace_isolation", "Repository isolates workspaces",
                ok, "create/list/get isolation", hard_blocker=True,
            )

        return [
            _guard("approval_item_model", "ApprovalItem production fields are present", approval_model, hard_blocker=True),
            _guard("review_item_model", "ReviewItem production fields are present", review_model, hard_blocker=True),
            _guard("status_transitions", "Review and approval transitions are validated", transitions, hard_blocker=True),
            _guard("optimistic_versioning", "Stale item versions are rejected", versioning, hard_blocker=True),
            _guard("workspace_isolation", "Repository isolates workspaces", workspace_isolation, hard_blocker=True),
        ]

    # -- foundation (existing e2e gate) -----------------------------------

    def _foundation_checks(self) -> list[GateCheck]:
        try:
            report = run_review_approval_gate(self.project_root)
        except Exception as exc:  # noqa: BLE001
            return [GateCheck("e2e_foundation", "E2E approval foundation", False, f"gate_error:{exc}", hard_blocker=True)]
        rows = report.get("checks", [])
        if not rows:
            return [GateCheck("e2e_foundation", "E2E approval foundation", False, str(report.get("blockers")), hard_blocker=True)]
        checks = []
        for row in rows:
            status = row.get("status")
            checks.append(
                GateCheck(
                    check_id=str(row.get("check_id")),
                    title=str(row.get("title") or row.get("check_id")),
                    passed=status == PASS,
                    detail=str(row.get("detail") or ""),
                    hard_blocker=status == BLOCKED,
                )
            )
        return checks

    # -- memory governance ------------------------------------------------

    def _memory_checks(self, root: Path) -> list[GateCheck]:
        from secondbrain.agent.memory_extractor import MemoryExtractor
        from secondbrain.agent.memory_service import GovernanceDecision, GovernedMemoryService
        from secondbrain.agent.privacy import PrivacyMode

        extractor = MemoryExtractor()

        def sensitive_blocked() -> GateCheck:
            service = GovernedMemoryService(project_root=root)
            outcome = service.submit(extractor.extract("Diagnose Depression, Sertralin", source_id="c", workspace_id="w1", confidence=0.95))
            ok = outcome.decision is GovernanceDecision.REVIEW and not service.store.list()
            return GateCheck("memory_sensitive_blocked", "Sensitive memory writes require review", ok, f"decision={outcome.decision.value}", hard_blocker=True)

        def privacy_blocked() -> GateCheck:
            service = GovernedMemoryService(project_root=root, privacy_mode=PrivacyMode.STRICT)
            outcome = service.submit(extractor.extract("Beliebige Notiz", source_id="c", workspace_id="w1", confidence=0.95))
            ok = outcome.decision is GovernanceDecision.BLOCKED and not service.store.list()
            return GateCheck("memory_privacy_mode_blocked", "Privacy mode blocks memory writes", ok, f"decision={outcome.decision.value}", hard_blocker=True)

        def no_secret_leak() -> GateCheck:
            service = GovernedMemoryService(project_root=root)
            outcome = service.submit(extractor.extract("password=hunter2_TOPSECRET", source_id="c", workspace_id="w1", confidence=0.95))
            blob = json.dumps(service.audit.records(), ensure_ascii=False)
            ok = outcome.decision is GovernanceDecision.BLOCKED and "hunter2_TOPSECRET" not in blob
            return GateCheck("memory_no_secret_leak", "Secrets never reach memory or audit", ok, "secret redacted", hard_blocker=True)

        def evidence_present() -> GateCheck:
            candidate = extractor.extract("Fakt mit Beleg", source_id="c", workspace_id="w1", confidence=0.95, evidence=[{"source": "c", "quote": "..."}])
            ok = candidate.has_evidence
            return GateCheck("memory_evidence_present", "Memory candidates carry evidence", ok, f"evidence={len(candidate.evidence)}", hard_blocker=False)

        return [
            _guard("memory_sensitive_blocked", "Sensitive memory writes require review", sensitive_blocked, hard_blocker=True),
            _guard("memory_privacy_mode_blocked", "Privacy mode blocks memory writes", privacy_blocked, hard_blocker=True),
            _guard("memory_no_secret_leak", "Secrets never reach memory or audit", no_secret_leak, hard_blocker=True),
            _guard("memory_evidence_present", "Memory candidates carry evidence", evidence_present, hard_blocker=False),
        ]

    # -- notifications ----------------------------------------------------

    def _notification_checks(self, root: Path) -> list[GateCheck]:
        from secondbrain.agent.review_service import UnifiedReviewInbox
        from secondbrain.native.approval import NativeApprovalQueue
        from secondbrain.notifications.review_notifications import NotificationPriority

        def risky_notification() -> GateCheck:
            base = root / "notif"
            NativeApprovalQueue(base).create(command="records.delete", intent="del", text="Del", category="delete_request", risk_level="high")
            notifications = UnifiedReviewInbox(base).evaluate_notifications(now=datetime.now(timezone.utc))
            ok = any(n.priority in {NotificationPriority.HIGH, NotificationPriority.CRITICAL} for n in notifications)
            return GateCheck("notifications_risky_alert", "Risky approvals raise notifications", ok, f"count={len(notifications)}", hard_blocker=False)

        def escalation() -> GateCheck:
            from secondbrain.notifications.review_notifications import NotificationType, ReviewNotificationService, TimeRules

            service = ReviewNotificationService(time_rules=TimeRules())
            now = datetime(2026, 1, 1, tzinfo=timezone.utc)
            item = {"item_id": "x", "item_type": "review", "category": "failed_import", "status": "pending", "risk_level": "write", "created_at": (now - timedelta(hours=6)).isoformat(), "title": "x", "deferred_until": "", "change_type": ""}
            notifications = service.evaluate([item], now=now)
            ok = any(n.type is NotificationType.REVIEW_OVERDUE for n in notifications)
            return GateCheck("notifications_escalation", "Overdue items escalate", ok, "review_overdue emitted", hard_blocker=False)

        return [
            _guard("notifications_risky_alert", "Risky approvals raise notifications", risky_notification, hard_blocker=False),
            _guard("notifications_escalation", "Overdue items escalate", escalation, hard_blocker=False),
        ]

    # -- metrics ----------------------------------------------------------

    def _metrics_checks(self, root: Path) -> list[GateCheck]:
        from secondbrain.metrics.review_approval_metrics import ReviewApprovalMetrics
        from secondbrain.native.approval import NativeApprovalQueue

        def no_secret_leak() -> GateCheck:
            base = root / "metrics"
            NativeApprovalQueue(base).create(command="connector.push", intent="send", text="Send", category="external_send", risk_level="high", payload={"password": "hunter2_SECRET"})
            blob = json.dumps(ReviewApprovalMetrics(base).export(), ensure_ascii=False)
            ok = "hunter2_SECRET" not in blob and "payload" not in blob
            return GateCheck("metrics_no_secret_leak", "Metrics export excludes secrets and payloads", ok, "clean export", hard_blocker=True)

        def computable() -> GateCheck:
            base = root / "metrics"
            result = ReviewApprovalMetrics(base).compute()
            ok = "created_total" in result.volume and "approval_rate" in result.quality
            return GateCheck("metrics_computable", "Governance metrics are computable", ok, "volume+quality present", hard_blocker=False)

        return [
            _guard("metrics_no_secret_leak", "Metrics export excludes secrets and payloads", no_secret_leak, hard_blocker=True),
            _guard("metrics_computable", "Governance metrics are computable", computable, hard_blocker=False),
        ]

    # -- concurrency ------------------------------------------------------

    def _concurrency_checks(self, root: Path) -> list[GateCheck]:
        from secondbrain.native.approval import ApprovalConcurrencyError, ExecutionTokenError, NativeApprovalQueue

        def single_execution() -> GateCheck:
            queue = NativeApprovalQueue(root / "concurrency")
            approval_id = queue.create(command="records.delete", intent="del", text="Del", category="delete_request", risk_level="high")["approval_id"]

            def approve(_: int) -> bool:
                try:
                    queue.transition(approval_id, "approved", actor="r", expected_version=0)
                    return True
                except (ApprovalConcurrencyError, ValueError):
                    return False

            with ThreadPoolExecutor(max_workers=2) as pool:
                accepted = sum(pool.map(approve, range(2)))
            queue.begin_execution(approval_id, executor_id="w1")
            double = False
            try:
                queue.begin_execution(approval_id, executor_id="w2")
                double = True
            except (ApprovalConcurrencyError, ExecutionTokenError):
                double = False
            ok = accepted == 1 and not double
            return GateCheck("no_double_execution", "Parallel approvals yield a single execution", ok, f"accepted={accepted}; double={double}", hard_blocker=True)

        def stale_rejected() -> GateCheck:
            queue = NativeApprovalQueue(root / "concurrency2")
            approval_id = queue.create(command="records.delete", intent="del", text="Del", category="delete_request", risk_level="high")["approval_id"]
            queue.transition(approval_id, "approved", actor="r")
            rejected = False
            try:
                queue.transition(approval_id, "executing", actor="r", expected_version=0)
            except ApprovalConcurrencyError:
                rejected = True
            return GateCheck("parallel_decision_conflict_safe", "Stale versions are rejected", rejected, "compare-and-set enforced", hard_blocker=True)

        return [
            _guard("no_double_execution", "Parallel approvals yield a single execution", single_execution, hard_blocker=True),
            _guard("parallel_decision_conflict_safe", "Stale versions are rejected", stale_rejected, hard_blocker=True),
        ]

    # -- crash recovery ---------------------------------------------------

    def _recovery_checks(self, root: Path) -> list[GateCheck]:
        from secondbrain.native.approval import NativeApprovalQueue, approval_path

        def stale_lease() -> GateCheck:
            queue = NativeApprovalQueue(root / "recovery")
            approval_id = queue.create(command="records.delete", intent="del", text="Del", category="delete_request", risk_level="high")["approval_id"]
            queue.transition(approval_id, "approved", actor="r")
            queue.begin_execution(approval_id, executor_id="w1", lease_seconds=1)
            queue.recover_stale_leases(now=datetime.now(timezone.utc) + timedelta(hours=1))
            ok = queue.get(approval_id)["status"] == "recovery_required"
            return GateCheck("crash_recovery_status", "Crashed executions become recovery_required", ok, "lease recovered", hard_blocker=False)

        def backup_restore() -> GateCheck:
            base = root / "recovery2"
            queue = NativeApprovalQueue(base)
            approval_id = queue.create(command="records.delete", intent="del", text="Del", category="delete_request", risk_level="high")["approval_id"]
            queue.transition(approval_id, "approved", actor="r")
            approval_path(base).write_text("total garbage\n", encoding="utf-8")
            item = queue.get(approval_id)
            ok = item is not None and item.get("approval_id") == approval_id
            return GateCheck("corrupt_queue_recoverable", "Corrupt queue restores from backup", ok, "restored from .bak", hard_blocker=True)

        return [
            _guard("crash_recovery_status", "Crashed executions become recovery_required", stale_lease, hard_blocker=False),
            _guard("corrupt_queue_recoverable", "Corrupt queue restores from backup", backup_restore, hard_blocker=True),
        ]

    # -- repository health ------------------------------------------------

    def _repository_checks(self, root: Path) -> list[GateCheck]:
        from secondbrain.repositories.jsonl_review_approval_repository import JsonlReviewApprovalRepository
        from secondbrain.repositories.postgres_review_approval_repository import PostgresReviewApprovalRepository
        from secondbrain.repositories.review_approval_repository import RepositoryConflict, resolve_backend
        from secondbrain.storage.db_executor import SqliteExecutor

        configured = resolve_backend()
        jsonl_prod = JsonlReviewApprovalRepository(root / "repo", production=True).health()
        pg = PostgresReviewApprovalRepository(SqliteExecutor(":memory:"))
        pg.ensure_schema()
        pg_health = pg.health()
        self.backend_status = {
            "configured_backend": configured,
            "jsonl_production_degraded": jsonl_prod.degraded,
            "postgres_healthy": pg_health.healthy,
        }

        def workspace_isolation() -> GateCheck:
            pg.create_approval(command="records.delete", intent="del", text="A", category="delete_request", risk_level="high", workspace_id="w1")
            pg.create_approval(command="records.delete", intent="del", text="B", category="delete_request", risk_level="high", workspace_id="w2")
            ok = len(pg.list_items(workspace_id="w1")) == 1 and len(pg.list_items(workspace_id="w2")) == 1
            return GateCheck("workspace_isolation", "Repository isolates workspaces", ok, "per-workspace listing", hard_blocker=True)

        def health_degraded() -> GateCheck:
            ok = jsonl_prod.degraded is True and jsonl_prod.healthy is True
            return GateCheck("repository_health", "JSONL is marked degraded in production", ok, f"backend={configured}", hard_blocker=False)

        return [
            _guard("workspace_isolation", "Repository isolates workspaces", workspace_isolation, hard_blocker=True),
            _guard("repository_health", "JSONL is marked degraded in production", health_degraded, hard_blocker=False),
        ]

    # -- metrics snapshot -------------------------------------------------

    def _collect_metrics(self, root: Path) -> dict[str, Any]:
        try:
            from secondbrain.metrics.review_approval_metrics import ReviewApprovalMetrics

            return ReviewApprovalMetrics(root / "metrics").export()
        except Exception as exc:  # noqa: BLE001
            return {"error": f"metrics_error:{type(exc).__name__}"}


def run_review_approval_release_gate(project_root: str | Path = ".", *, write_report: bool = True) -> dict[str, Any]:
    """Public launcher/test entrypoint. Always returns a controlled verdict."""

    try:
        return ReviewApprovalReleaseGate(project_root).run(write_report=write_report)
    except Exception as exc:  # noqa: BLE001
        return {
            "schema": SCHEMA,
            "version": RELEASE_VERSION,
            "timestamp": _utc_now(),
            "overall_status": BLOCKED,
            "ok": False,
            "summary": {"total": 0, "passed": 0, "conditional": 0, "blocked": 1},
            "checks": [],
            "blockers": [f"release_gate_internal_error:{type(exc).__name__}:{exc}"],
            "warnings": [],
            "metrics": {},
            "test_commands": TEST_COMMANDS,
            "backend_status": {},
            "security_summary": {},
        }
