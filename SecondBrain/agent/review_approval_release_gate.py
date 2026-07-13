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
    "python launcher.py review-approval-release-gate",
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

_NONCRITICAL_WARNING_IDS = {
    "viewmodel_visible",
    "corrupt_queue_controlled",
    "metrics_computable",
    "gui_inbox_reachable",
    "gui_badge_correct",
    "gui_decisions",
    "gui_error_state",
    "gui_no_technical_ids",
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
        return GateCheck(check_id, title, False, f"check_error:{type(exc).__name__}", hard_blocker=hard_blocker)


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
            check_id = str(row.get("check_id"))
            checks.append(
                GateCheck(
                    check_id=check_id,
                    title=str(row.get("title") or row.get("check_id")),
                    passed=status == PASS,
                    detail=str(row.get("detail") or ""),
                    hard_blocker=(
                        status == BLOCKED
                        or (status != PASS and check_id not in _NONCRITICAL_WARNING_IDS)
                    ),
                )
            )
        return checks

    # -- import governance ------------------------------------------------

    def _import_checks(self, root: Path) -> list[GateCheck]:
        from secondbrain.import_pipeline import ImportStatus, UnifiedImportPipeline

        def classification(*, confidence: float = 0.95, sensitive: bool = False) -> dict[str, Any]:
            return {
                "document_type": "vertrag",
                "tags": ["gate"],
                "confidence": confidence,
                "needs_review": confidence < 0.6,
                "sensitive": sensitive,
                "pii": {
                    "findings": [{"type": "api_key", "count": 1}] if sensitive else [],
                    "markers": [],
                },
                "classification_conflict": False,
            }

        class FailedParser:
            def parse(self, path: Path):
                class Parsed:
                    text = ""
                    title = path.name
                    errors = ["parser aborted: corrupted file"]
                    metadata = {"parser": "release-gate-parser"}

                    class Status:
                        value = "failed"

                    status = Status()

                return Parsed()

        def pipeline(base: Path, *, classifier: Callable[[str], dict[str, Any]], parser: Any = None):
            index_calls: list[dict[str, Any]] = []
            instance = UnifiedImportPipeline(
                base,
                classifier=classifier,
                parser_registry=parser,
                indexer=lambda text, metadata: index_calls.append(dict(metadata)) or {"ok": True},
            )
            return instance, index_calls

        def failed_review() -> GateCheck:
            base = root / "import-failed"
            source = base / "broken.bin"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(b"broken")
            instance, calls = pipeline(base, classifier=lambda text: classification(), parser=FailedParser())
            job = instance.process(instance.submit_file(source).job_id)
            reviews = instance.review_inbox.reviews.list()
            ok = (
                job.status == ImportStatus.FAILED_REVIEWABLE
                and len(reviews) == 1
                and reviews[0].get("category") == "failed_import"
                and not calls
            )
            return GateCheck(
                "import_failed_review", "Failed imports enter review",
                ok, f"status={job.status}; reviews={len(reviews)}", hard_blocker=True,
            )

        def sensitive_review() -> GateCheck:
            instance, calls = pipeline(
                root / "import-sensitive",
                classifier=lambda text: classification(sensitive=True),
            )
            job = instance.process(instance.submit_text("credential material", source_ref="gate://sensitive").job_id)
            reviews = instance.review_inbox.reviews.list()
            ok = (
                job.status == ImportStatus.REVIEW_REQUIRED
                and job.memory_forwarding_blocked
                and job.connector_forwarding_blocked
                and len(reviews) == 1
                and reviews[0].get("category") == "sensitive_document"
                and not calls
            )
            return GateCheck(
                "import_sensitive_review", "Sensitive imports block forwarding",
                ok, f"status={job.status}; reviews={len(reviews)}", hard_blocker=True,
            )

        def low_confidence_review() -> GateCheck:
            instance, calls = pipeline(
                root / "import-low", classifier=lambda text: classification(confidence=0.2)
            )
            job = instance.process(instance.submit_text("uncertain", source_ref="gate://low").job_id)
            reviews = instance.review_inbox.reviews.list()
            ok = (
                job.status == ImportStatus.REVIEW_REQUIRED
                and job.classification_blocked
                and len(reviews) == 1
                and reviews[0].get("category") == "low_confidence_classification"
                and not calls
            )
            return GateCheck(
                "import_low_confidence_review", "Low-confidence imports require review",
                ok, f"status={job.status}; reviews={len(reviews)}", hard_blocker=True,
            )

        def approve_resumes() -> GateCheck:
            instance, calls = pipeline(
                root / "import-approve", classifier=lambda text: classification(confidence=0.2)
            )
            waiting = instance.process(instance.submit_text("approve", source_ref="gate://approve").job_id)
            completed = instance.approve_review(waiting.review_id, "gate-reviewer")
            repeated = instance.process(completed.job_id)
            ok = completed.status == repeated.status == ImportStatus.INDEXED and len(calls) == 1
            return GateCheck(
                "import_approve_resumes", "Approved import resumes exactly once",
                ok, f"status={completed.status}; index_calls={len(calls)}", hard_blocker=True,
            )

        def reject_stops() -> GateCheck:
            instance, calls = pipeline(
                root / "import-reject", classifier=lambda text: classification(confidence=0.2)
            )
            waiting = instance.process(instance.submit_text("reject", source_ref="gate://reject").job_id)
            rejected = instance.reject_review(waiting.review_id, "gate-reviewer")
            stopped = instance.process(rejected.job_id)
            ok = rejected.status == stopped.status == ImportStatus.REJECTED and not calls
            return GateCheck(
                "import_reject_stops", "Rejected import never indexes",
                ok, f"status={rejected.status}; index_calls={len(calls)}", hard_blocker=True,
            )

        def defer_pauses() -> GateCheck:
            instance, calls = pipeline(
                root / "import-defer", classifier=lambda text: classification(confidence=0.2)
            )
            waiting = instance.process(instance.submit_text("defer", source_ref="gate://defer").job_id)
            deferred = instance.defer_review(
                waiting.review_id, "gate-reviewer", until="2099-01-01T00:00:00+00:00"
            )
            paused = instance.process(deferred.job_id)
            ok = deferred.status == paused.status == ImportStatus.REVIEW_DEFERRED and not calls
            return GateCheck(
                "import_defer_pauses", "Deferred import remains paused",
                ok, f"status={deferred.status}; index_calls={len(calls)}", hard_blocker=True,
            )

        def no_duplicates() -> GateCheck:
            instance, _ = pipeline(
                root / "import-dedupe", classifier=lambda text: classification(confidence=0.2)
            )
            waiting = instance.process(instance.submit_text("retry", source_ref="gate://retry").job_id)
            instance.retry(waiting.job_id)
            instance.process(waiting.job_id)
            reviews = instance.review_inbox.reviews.list()
            ok = len(reviews) == 1 and reviews[0].get("review_id") == waiting.review_id
            return GateCheck(
                "import_no_duplicates", "Import retry does not duplicate review items",
                ok, f"reviews={len(reviews)}", hard_blocker=True,
            )

        checks = (
            ("import_failed_review", "Failed imports enter review", failed_review),
            ("import_sensitive_review", "Sensitive imports block forwarding", sensitive_review),
            ("import_low_confidence_review", "Low-confidence imports require review", low_confidence_review),
            ("import_approve_resumes", "Approved import resumes exactly once", approve_resumes),
            ("import_reject_stops", "Rejected import never indexes", reject_stops),
            ("import_defer_pauses", "Deferred import remains paused", defer_pauses),
            ("import_no_duplicates", "Import retry does not duplicate review items", no_duplicates),
        )
        return [_guard(check_id, title, function, hard_blocker=True) for check_id, title, function in checks]

    # -- memory governance ------------------------------------------------

    def _memory_checks(self, root: Path) -> list[GateCheck]:
        from secondbrain.agent.memory_extractor import MemoryExtractor
        from secondbrain.agent.memory_service import GovernanceDecision, GovernedMemoryService
        from secondbrain.agent.privacy import PrivacyMode
        from secondbrain.agent.review_service import UnifiedReviewInbox

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

        def low_confidence_review() -> GateCheck:
            service = GovernedMemoryService(project_root=root / "low-memory")
            outcome = service.submit(
                extractor.extract(
                    "Unbelegte persoenliche Praeferenz",
                    source_id="unknown",
                    workspace_id="w1",
                    confidence=0.2,
                )
            )
            ok = outcome.decision is GovernanceDecision.REVIEW and not service.store.list()
            return GateCheck(
                "memory_low_confidence_review", "Low-confidence memory requires review",
                ok, f"decision={outcome.decision.value}", hard_blocker=True,
            )

        def no_secret_leak() -> GateCheck:
            service = GovernedMemoryService(project_root=root)
            outcome = service.submit(extractor.extract("password=hunter2_TOPSECRET", source_id="c", workspace_id="w1", confidence=0.95))
            blob = json.dumps(service.audit.records(), ensure_ascii=False)
            ok = outcome.decision is GovernanceDecision.BLOCKED and "hunter2_TOPSECRET" not in blob
            return GateCheck("memory_no_secret_leak", "Secrets never reach memory or audit", ok, "secret redacted", hard_blocker=True)

        def evidence_present() -> GateCheck:
            candidate = extractor.extract("Fakt mit Beleg", source_id="c", workspace_id="w1", confidence=0.95, evidence=[{"source": "c", "quote": "..."}])
            ok = candidate.has_evidence
            return GateCheck("memory_evidence_present", "Memory candidates carry evidence", ok, f"evidence={len(candidate.evidence)}", hard_blocker=True)

        def approve_once() -> GateCheck:
            base = root / "memory-approve"
            inbox = UnifiedReviewInbox(base)
            service = GovernedMemoryService(
                project_root=base,
                inbox=inbox,
            )
            outcome = service.submit(
                extractor.extract(
                    "Kontostand negativ, Finanzplanung erforderlich",
                    source_id="doc:finance",
                    workspace_id="w1",
                    confidence=0.95,
                )
            )
            if outcome.decision is not GovernanceDecision.REVIEW:
                return GateCheck(
                    "memory_approve_once", "Approved memory is stored exactly once",
                    False, f"initial={outcome.decision.value}", hard_blocker=True,
                )
            inbox.approve(outcome.review_id, "gate-reviewer")
            repeated = service.apply_memory_decision(
                outcome.candidate_id, "approved", actor="gate-reviewer"
            )
            ok = len(service.store.list()) == 1 and repeated.decision is GovernanceDecision.DUPLICATE
            return GateCheck(
                "memory_approve_once", "Approved memory is stored exactly once",
                ok, f"memories={len(service.store.list())}; repeated={repeated.decision.value}",
                hard_blocker=True,
            )

        return [
            _guard("memory_sensitive_blocked", "Sensitive memory writes require review", sensitive_blocked, hard_blocker=True),
            _guard("memory_low_confidence_review", "Low-confidence memory requires review", low_confidence_review, hard_blocker=True),
            _guard("memory_privacy_mode_blocked", "Privacy mode blocks memory writes", privacy_blocked, hard_blocker=True),
            _guard("memory_no_secret_leak", "Secrets never reach memory or audit", no_secret_leak, hard_blocker=True),
            _guard("memory_approve_once", "Approved memory is stored exactly once", approve_once, hard_blocker=True),
            _guard("memory_evidence_present", "Memory candidates carry evidence", evidence_present, hard_blocker=True),
        ]

    # -- connector governance --------------------------------------------

    def _connector_checks(self, root: Path) -> list[GateCheck]:
        from secondbrain.agent.approval_service import AgentApprovalService
        from secondbrain.connectors.scaffold.approval import (
            ApprovalBindingMismatch,
            ApprovalConflict,
            ApprovalExpired,
            ApprovalGate,
            ApprovalRequired,
            ConnectorActionPolicy,
        )

        def gate_for(name: str, *, now: float = 1_000.0):
            state = {"now": now}
            service = AgentApprovalService(root / name)
            gate = ApprovalGate(
                approval_service=service,
                connector_id="gmail",
                workspace_id="workspace-1",
                actor="gate-user",
                effective_scopes=("mail.read",),
                approval_ttl_seconds=60,
                clock=lambda: state["now"],
            )
            return gate, service, state

        def request(gate: Any, **overrides: Any):
            values = {
                "action": "oauth.scope.update",
                "resource": "gmail",
                "method": "POST",
                "target": "oauth",
                "payload": {"requested": ["mail.read", "mail.send"]},
                "requested_scopes": ("mail.read", "mail.send"),
                "execute": lambda: "changed",
            }
            values.update(overrides)
            try:
                gate.guard(**values)
            except ApprovalRequired as exc:
                return exc.request, values
            raise AssertionError("connector_action_was_not_blocked")

        def credential_change() -> GateCheck:
            decision = ConnectorActionPolicy().evaluate(
                connector_id="gmail",
                action="oauth.credentials.rotate",
                method="POST",
                action_type="credential_change",
            )
            ok = decision.requires_approval and decision.approval_category == "connector_permission_change"
            return GateCheck(
                "credential_change_requires_approval", "Credential changes require approval",
                ok, f"action={decision.action_type}; category={decision.approval_category}",
                hard_blocker=True,
            )

        def scope_change() -> GateCheck:
            decision = ConnectorActionPolicy().evaluate(
                connector_id="gmail",
                action="oauth.scope.update",
                method="GET",
                effective_scopes=("mail.read",),
                requested_scopes=("mail.read", "mail.send"),
            )
            ok = decision.requires_approval and decision.added_scopes == ("mail.send",)
            return GateCheck(
                "scope_change_requires_approval", "Scope expansion requires approval",
                ok, f"added={','.join(decision.added_scopes)}", hard_blocker=True,
            )

        def confirmed_blocked() -> GateCheck:
            gate, service, _ = gate_for("confirmed")
            calls: list[str] = []
            blocked = False
            try:
                gate.guard(
                    action="gmail.send", resource="gmail", method="POST",
                    target="recipient", payload={"subject": "gate"}, confirmed=True,
                    execute=lambda: calls.append("sent"),
                )
            except ApprovalRequired:
                blocked = True
            ok = blocked and not calls and len(service.list_pending()) == 1
            return GateCheck(
                "confirmed_boolean_blocked", "confirmed=True cannot bypass persistence",
                ok, f"blocked={blocked}; calls={len(calls)}", hard_blocker=True,
            )

        def scope_diff_bound() -> GateCheck:
            gate, service, _ = gate_for("scope")
            approval, _ = request(gate)
            stored = service.get(approval.request_id) or {}
            payload = stored.get("payload") if isinstance(stored.get("payload"), dict) else {}
            ok = (
                payload.get("existing_scopes") == ["mail.read"]
                and payload.get("requested_scopes") == ["mail.read", "mail.send"]
                and payload.get("scope_diff") == {"added": ["mail.send"], "removed": []}
            )
            return GateCheck(
                "connector_scope_diff_bound", "Connector approval binds exact scope diff",
                ok, f"scope_diff={payload.get('scope_diff')}", hard_blocker=True,
            )

        def payload_bound() -> GateCheck:
            gate, _, _ = gate_for("payload")
            approval, values = request(gate)
            gate.approve(approval.request_id, actor="gate-reviewer")
            blocked = False
            try:
                gate.guard(
                    **{
                        **values,
                        "payload": {"requested": ["mail.read", "mail.send"], "changed": True},
                        "approval_id": approval.request_id,
                    }
                )
            except ApprovalBindingMismatch:
                blocked = True
            return GateCheck(
                "connector_payload_bound", "Connector approval binds payload hash",
                blocked, f"changed_payload_blocked={blocked}", hard_blocker=True,
            )

        def workspace_bound() -> GateCheck:
            gate, _, _ = gate_for("workspace")
            approval, values = request(gate)
            gate.approve(approval.request_id, actor="gate-reviewer")
            blocked = False
            try:
                gate.guard(
                    **{**values, "workspace_id": "workspace-2", "approval_id": approval.request_id}
                )
            except ApprovalBindingMismatch:
                blocked = True
            return GateCheck(
                "connector_workspace_bound", "Connector approval binds workspace",
                blocked, f"workspace_mismatch_blocked={blocked}", hard_blocker=True,
            )

        def expiration() -> GateCheck:
            gate, _, state = gate_for("expiration")
            calls: list[str] = []
            approval, values = request(gate, execute=lambda: calls.append("changed"))
            gate.approve(approval.request_id, actor="gate-reviewer")
            state["now"] += 61
            blocked = False
            try:
                gate.guard(**{**values, "approval_id": approval.request_id})
            except ApprovalExpired:
                blocked = True
            ok = blocked and not calls
            return GateCheck(
                "connector_expiration_enforced", "Expired connector approval is rejected",
                ok, f"blocked={blocked}; calls={len(calls)}", hard_blocker=True,
            )

        def single_use() -> GateCheck:
            gate, _, _ = gate_for("single-use")
            calls: list[str] = []
            approval, values = request(gate, execute=lambda: calls.append("changed") or "changed")
            gate.approve(approval.request_id, actor="gate-reviewer")
            first = gate.guard(**{**values, "approval_id": approval.request_id})
            blocked = False
            try:
                gate.guard(**{**values, "approval_id": approval.request_id})
            except ApprovalConflict:
                blocked = True
            ok = first == "changed" and blocked and calls == ["changed"]
            return GateCheck(
                "connector_single_use", "Connector approval is consumed exactly once",
                ok, f"calls={len(calls)}; repeated_blocked={blocked}", hard_blocker=True,
            )

        checks = (
            ("credential_change_requires_approval", "Credential changes require approval", credential_change),
            ("scope_change_requires_approval", "Scope expansion requires approval", scope_change),
            ("confirmed_boolean_blocked", "confirmed=True cannot bypass persistence", confirmed_blocked),
            ("connector_scope_diff_bound", "Connector approval binds exact scope diff", scope_diff_bound),
            ("connector_payload_bound", "Connector approval binds payload hash", payload_bound),
            ("connector_workspace_bound", "Connector approval binds workspace", workspace_bound),
            ("connector_expiration_enforced", "Expired connector approval is rejected", expiration),
            ("connector_single_use", "Connector approval is consumed exactly once", single_use),
        )
        return [_guard(check_id, title, function, hard_blocker=True) for check_id, title, function in checks]

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
            return GateCheck("notifications_risky_alert", "Risky approvals raise notifications", ok, f"count={len(notifications)}", hard_blocker=True)

        def escalation() -> GateCheck:
            from secondbrain.notifications.review_notifications import NotificationType, ReviewNotificationService, TimeRules

            service = ReviewNotificationService(time_rules=TimeRules())
            now = datetime(2026, 1, 1, tzinfo=timezone.utc)
            item = {"item_id": "x", "item_type": "review", "category": "failed_import", "status": "pending", "risk_level": "write", "created_at": (now - timedelta(hours=6)).isoformat(), "title": "x", "deferred_until": "", "change_type": ""}
            notifications = service.evaluate([item], now=now)
            ok = any(n.type is NotificationType.REVIEW_OVERDUE for n in notifications)
            return GateCheck("notifications_escalation", "Overdue items escalate", ok, "review_overdue emitted", hard_blocker=True)

        return [
            _guard("notifications_risky_alert", "Risky approvals raise notifications", risky_notification, hard_blocker=True),
            _guard("notifications_escalation", "Overdue items escalate", escalation, hard_blocker=True),
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
            return GateCheck("crash_recovery_status", "Crashed executions become recovery_required", ok, "lease recovered", hard_blocker=True)

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
            _guard("crash_recovery_status", "Crashed executions become recovery_required", stale_lease, hard_blocker=True),
            _guard("corrupt_queue_recoverable", "Corrupt queue restores from backup", backup_restore, hard_blocker=True),
        ]

    # -- repository health ------------------------------------------------

    def _repository_checks(self, root: Path) -> list[GateCheck]:
        from secondbrain.repositories.jsonl_review_approval_repository import (
            JsonlReviewApprovalRepository,
        )
        from secondbrain.repositories.review_approval_repository import (
            RepositoryUnavailable,
            create_review_approval_repository,
            resolve_backend,
        )

        configured = resolve_backend(self.env)
        jsonl_prod = JsonlReviewApprovalRepository(
            root / "repo-jsonl", production=True
        ).health()
        self.backend_status = {
            "configured_backend": configured,
            "jsonl_production_degraded": jsonl_prod.degraded,
            "jsonl_gate_status": jsonl_prod.gate_status,
            "postgres_healthy": False,
            "postgres_detail": "not_checked",
            "production_eligible": False,
            "gate_status": BLOCKED,
        }

        def production_backend() -> GateCheck:
            ok = configured == "postgres"
            detail = (
                "postgres configured"
                if ok
                else "jsonl is development-only and cannot certify production"
            )
            return GateCheck(
                "production_backend", "Production uses PostgreSQL review/approval backend",
                ok, detail, hard_blocker=True,
            )

        def postgresql_health() -> GateCheck:
            if configured != "postgres":
                return GateCheck(
                    "postgresql_health", "Configured PostgreSQL backend is reachable",
                    False, "postgres backend is not configured", hard_blocker=True,
                )
            try:
                repository = create_review_approval_repository(
                    root / "repo-postgres",
                    env=self.env,
                    executor=self.repository_executor,
                )
                health = repository.health()
                ok = (
                    repository.backend == "postgres"
                    and health.healthy
                    and not health.degraded
                )
                self.backend_status.update(
                    postgres_healthy=health.healthy,
                    postgres_detail=health.detail,
                    production_eligible=ok,
                    gate_status=PASS if ok else BLOCKED,
                )
                return GateCheck(
                    "postgresql_health", "Configured PostgreSQL backend is reachable",
                    ok, f"backend={repository.backend}; healthy={health.healthy}",
                    hard_blocker=True,
                )
            except RepositoryUnavailable as exc:
                self.backend_status.update(
                    postgres_healthy=False,
                    postgres_detail=type(exc).__name__,
                    production_eligible=False,
                    gate_status=BLOCKED,
                )
                return GateCheck(
                    "postgresql_health", "Configured PostgreSQL backend is reachable",
                    False, f"postgres unavailable:{type(exc).__name__}", hard_blocker=True,
                )

        def repository_health() -> GateCheck:
            jsonl_policy_ok = jsonl_prod.gate_status == CONDITIONAL_PASS
            backend_ok = bool(self.backend_status.get("production_eligible"))
            ok = jsonl_policy_ok and backend_ok
            return GateCheck(
                "repository_health", "Repository health and fallback policy are enforced",
                ok,
                f"jsonl={jsonl_prod.gate_status}; postgres={self.backend_status.get('gate_status')}",
                hard_blocker=True,
            )

        return [
            _guard("production_backend", "Production uses PostgreSQL review/approval backend", production_backend, hard_blocker=True),
            _guard("postgresql_health", "Configured PostgreSQL backend is reachable", postgresql_health, hard_blocker=True),
            _guard("repository_health", "Repository health and fallback policy are enforced", repository_health, hard_blocker=True),
        ]

    # -- GUI view model ---------------------------------------------------

    def _gui_checks(self, root: Path) -> list[GateCheck]:
        from secondbrain.gui.approval_inbox import (
            TAB_APPROVALS, TAB_COMPLETED, TAB_DEFERRED, ApprovalInboxViewModel,
        )
        from secondbrain.native.approval import NativeApprovalQueue, approval_path

        def create(base: Path, command: str = "records.delete", **fields: Any) -> dict[str, Any]:
            return NativeApprovalQueue(base).create(
                command=command, intent="gate_gui", text=f"Execute {command}",
                category="delete_request" if "delete" in command else "risky_agent_action",
                risk_level="high", plan_id="internal-plan-id", step_id="internal-step-id",
                tool_name=command, **fields,
            )

        def inbox_reachable() -> GateCheck:
            state = ApprovalInboxViewModel(root / "gui-empty").load(TAB_APPROVALS)
            ok = state.get("ok") is True and state.get("items") == []
            return GateCheck("gui_inbox_reachable", "GUI inbox loads without queue files", ok, f"ok={state.get('ok')}")

        def badge_correct() -> GateCheck:
            base = root / "gui-badge"
            create(base)
            create(base, command="agent.risky_action")
            state = ApprovalInboxViewModel(base).load(TAB_APPROVALS)
            ok = state.get("pending_count") == 2 and state.get("critical_count") >= 1
            return GateCheck("gui_badge_correct", "GUI badge reports open and critical items", ok, f"pending={state.get('pending_count')}; critical={state.get('critical_count')}")

        def decisions() -> GateCheck:
            base = root / "gui-decisions"
            approved = create(base, command="agent.approve")
            rejected = create(base, command="agent.reject")
            deferred = create(base, command="agent.defer")
            model = ApprovalInboxViewModel(base)
            model.approve(approved["approval_id"], note="approved")
            model.reject(rejected["approval_id"], note="rejected")
            model.defer(deferred["approval_id"], until="2099-01-01T00:00:00+00:00", note="later")
            completed = {item["item_id"] for item in model.load(TAB_COMPLETED)["items"]}
            deferred_ids = {item["item_id"] for item in model.load(TAB_DEFERRED)["items"]}
            ok = approved["approval_id"] in completed and rejected["approval_id"] in completed and deferred["approval_id"] in deferred_ids and model.load(TAB_APPROVALS)["items"] == []
            return GateCheck("gui_decisions", "GUI supports approve, reject and defer", ok, f"completed={len(completed)}; deferred={len(deferred_ids)}")

        def error_state() -> GateCheck:
            base = root / "gui-error"
            path = approval_path(base)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("{broken json\n", encoding="utf-8")
            state = ApprovalInboxViewModel(base).load()
            ok = state.get("ok") is False and state.get("empty_message") == "Fehler beim Laden"
            return GateCheck("gui_error_state", "GUI renders controlled queue errors", ok, f"status={state.get('status')}")

        def no_secret() -> GateCheck:
            base = root / "gui-secret"
            secret = "release-gate-secret-value"
            approval = create(base, command="mail.send", payload={"recipient": "person@example.com", "token": secret})
            NativeApprovalQueue(base).transition(approval["approval_id"], "deferred", actor="gate", note=f"hide {secret}")
            detail = ApprovalInboxViewModel(base).detail(approval["approval_id"])
            persisted = approval_path(base).read_text(encoding="utf-8")
            ok = secret not in json.dumps(detail, ensure_ascii=False) and secret not in persisted and detail["payload"]["token"] == "***"
            return GateCheck("gui_no_secret_leak", "GUI never renders raw secrets", ok, f"redacted={detail.get('payload', {}).get('token') == '***'}", hard_blocker=True)

        def no_technical_ids() -> GateCheck:
            base = root / "gui-identifiers"
            create(base)
            item = ApprovalInboxViewModel(base).load(TAB_APPROVALS)["items"][0]
            visible = sorted({"plan_id", "step_id", "approval_id", "review_id"}.intersection(item))
            return GateCheck("gui_no_technical_ids", "GUI main list hides technical identifiers", not visible, f"visible={','.join(visible) or 'none'}")

        checks = (
            ("gui_inbox_reachable", "GUI inbox loads without queue files", inbox_reachable, False),
            ("gui_badge_correct", "GUI badge reports open and critical items", badge_correct, False),
            ("gui_decisions", "GUI supports approve, reject and defer", decisions, False),
            ("gui_error_state", "GUI renders controlled queue errors", error_state, False),
            ("gui_no_secret_leak", "GUI never renders raw secrets", no_secret, True),
            ("gui_no_technical_ids", "GUI main list hides technical identifiers", no_technical_ids, False),
        )
        return [_guard(check_id, title, function, hard_blocker=hard) for check_id, title, function, hard in checks]

    # -- metrics snapshot -------------------------------------------------

    def _collect_metrics(self, root: Path) -> dict[str, Any]:
        try:
            from secondbrain.metrics.review_approval_metrics import ReviewApprovalMetrics

            return ReviewApprovalMetrics(root / "metrics").export()
        except Exception as exc:  # noqa: BLE001
            return {"error": f"metrics_error:{type(exc).__name__}"}


def run_review_approval_release_gate(
    project_root: str | Path = ".",
    *,
    write_report: bool = True,
    env: Mapping[str, str] | None = None,
    repository_executor: Any | None = None,
) -> dict[str, Any]:
    """Public launcher/test entrypoint. Always returns a controlled verdict."""

    try:
        return ReviewApprovalReleaseGate(
            project_root,
            env=env,
            repository_executor=repository_executor,
        ).run(write_report=write_report)
    except Exception as exc:  # noqa: BLE001
        report = {
            "schema": SCHEMA,
            "version": RELEASE_VERSION,
            "timestamp": _utc_now(),
            "overall_status": BLOCKED,
            "ok": False,
            "summary": {"total": 0, "passed": 0, "conditional": 0, "blocked": 1},
            "checks": [],
            "blockers": [f"release_gate_internal_error:{type(exc).__name__}"],
            "warnings": [],
            "metrics": {},
            "test_commands": TEST_COMMANDS,
            "backend_status": {},
            "security_summary": {},
            "release_recommendation": "DO_NOT_RELEASE",
        }
        if write_report:
            ReviewApprovalReleaseGate(project_root)._write_report(report)  # noqa: SLF001
        return report
