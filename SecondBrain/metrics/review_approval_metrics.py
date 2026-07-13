"""Governance metrics for the review/approval system.

Read-only aggregation over the review and approval queues plus the governance
audit logs. The computation never mutates state, never takes a lock and never
blocks queue processing; corrupted audit lines are skipped and counted rather
than raising.

Privacy guarantees for the export:

* no technical ids (approval_id / review_id) in any headline figure,
* no personal content, titles or payloads - only counts, rates and durations,
* a final secret sweep over the serialized export.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from secondbrain.agent.privacy import PrivacyDecision, PrivacyGuard, PrivacyMode

__all__ = ["ReviewApprovalMetrics", "MetricsResult"]

_SECRET_GUARD = PrivacyGuard(PrivacyMode.OFF)

_DECIDED = {"approved", "rejected", "deferred"}
_SEGMENT_DIMENSIONS = ("category", "tool", "connector", "workspace", "risk", "source")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _percentile(sorted_values: Sequence[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    rank = pct * (len(sorted_values) - 1)
    low = int(rank)
    high = min(low + 1, len(sorted_values) - 1)
    frac = rank - low
    return float(sorted_values[low] + (sorted_values[high] - sorted_values[low]) * frac)


@dataclass(frozen=True)
class MetricsResult:
    volume: dict[str, int]
    times: dict[str, float]
    security: dict[str, int]
    quality: dict[str, float]
    segments: dict[str, dict[str, int]]
    trends: dict[str, dict[str, int]]
    corrupted_audit_lines: int
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "secondbrain.metrics.review_approval.v2",
            "generated_at": self.generated_at,
            "volume": dict(self.volume),
            "times": dict(self.times),
            "security": dict(self.security),
            "quality": dict(self.quality),
            "segments": {dim: dict(counts) for dim, counts in self.segments.items()},
            "trends": {window: dict(counts) for window, counts in self.trends.items()},
            "corrupted_audit_lines": self.corrupted_audit_lines,
        }


class ReviewApprovalMetrics:
    def __init__(
        self,
        project_root: str | Path | None = None,
        *,
        inbox: Any | None = None,
        now: datetime | None = None,
    ) -> None:
        self._now = now
        self._corrupted = 0
        if inbox is not None:
            self.approvals_records = list(inbox.approvals.list())
            self.reviews_records = list(inbox.reviews.list())
            self.project_root = Path(inbox.approvals.project_root)
        else:
            self.project_root = Path(project_root or Path.cwd()).resolve()
            self.approvals_records = self._read_jsonl(self._native_path("approval_queue.jsonl"))[0]
            self.reviews_records = self._read_jsonl(self._native_path("review_queue.jsonl"))[0]
        self._base_corrupted = self._corrupted

    # -- public -----------------------------------------------------------

    def compute(self, *, window_days: int | None = None) -> MetricsResult:
        now = self._now or _utc_now()
        self._corrupted = self._base_corrupted
        items = self._items(window_days=window_days, now=now)

        volume = self._volume(items)
        times = self._times(items, now=now)
        quality = self._quality(items)
        segments = {dim: self._segment(items, dim) for dim in _SEGMENT_DIMENSIONS}
        segments["time_range"] = self._time_segment(items, now=now)
        trends = {
            "7d": self._window_volume(items, now=now, days=7),
            "30d": self._window_volume(items, now=now, days=30),
        }
        # Audit-derived counters (tolerant of missing/corrupt files).
        security, operational_quality = self._audit_metrics(items)
        quality.update(operational_quality)
        # Compatibility aliases used by the v30.78 dashboard/tests.
        quality.update(security)
        quality["duplicate_prevention_count"] = security["duplicate_execution_prevented_count"]
        quality["resume_failure_count"] = int(operational_quality["resume_failure_count"])

        return MetricsResult(
            volume=volume,
            times=times,
            security=security,
            quality=quality,
            segments=segments,
            trends=trends,
            corrupted_audit_lines=self._corrupted,
            generated_at=now.isoformat(timespec="seconds"),
        )

    def export(self, *, window_days: int | None = None) -> dict[str, Any]:
        """Metrics dict guaranteed free of ids, payloads and secrets."""

        return _scrub(self.compute(window_days=window_days).to_dict())

    def dashboard_view(self) -> dict[str, Any]:
        """Headline KPIs for dashboard cards - numbers and labels only."""

        now = self._now or _utc_now()
        result = self.compute()
        items = self._items(window_days=None, now=now)
        segments = result.segments["category"]
        most_common = max(segments.items(), key=lambda kv: kv[1])[0] if segments else ""
        open_items = sum(
            1 for item in items if item["status"] in {"pending", "deferred", "recovery_required"}
        )
        critical_items = self._critical_pending(now)
        overdue_items = self._overdue_pending(now)
        blocked_actions = result.security["blocked_unsafe_execution_count"]
        return _scrub(
            {
                "open_items": open_items,
                "critical_items": critical_items,
                "overdue_items": overdue_items,
                "blocked_unsafe_actions": blocked_actions,
                "open_approvals": result.volume["pending_approvals"],
                "critical_approvals": critical_items,
                "overdue_reviews": overdue_items,
                "average_decision_time": result.times["average_decision_time"],
                "blocked_unsafe_executions": blocked_actions,
                "most_common_category": most_common,
                "trend_7d": sum(result.trends["7d"].values()),
                "trend_30d": sum(result.trends["30d"].values()),
            }
        )

    # -- item model -------------------------------------------------------

    def _items(self, *, window_days: int | None, now: datetime) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for record in self.approvals_records:
            rows.append(self._normalize(record, kind="approval"))
        for record in self.reviews_records:
            rows.append(self._normalize(record, kind="review"))
        if window_days is not None:
            threshold = now - timedelta(days=window_days)
            rows = [row for row in rows if row["created_at"] is not None and row["created_at"] >= threshold]
        return rows

    def _normalize(self, record: Mapping[str, Any], *, kind: str) -> dict[str, Any]:
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        payload = record.get("payload") if isinstance(record.get("payload"), dict) else {}
        audit_events = [
            event
            for event in (record.get("decision_audit") or [])
            if isinstance(event, Mapping)
        ]
        decisions = {
            str(event.get("new_status") or "").strip().lower()
            for event in audit_events
            if event.get("new_status")
        }
        workspace = str(record.get("workspace_id") or metadata.get("workspace_id") or "") or "unassigned"
        tool = str(record.get("tool_name") or record.get("command") or "") or "none"
        connector = str(
            record.get("connector")
            or record.get("connector_id")
            or metadata.get("connector")
            or metadata.get("connector_id")
            or payload.get("connector")
            or payload.get("connector_id")
            or ""
        ) or "none"
        risk = str(record.get("risk_level") or metadata.get("risk_level") or "") or "unspecified"
        source = str(record.get("source") or metadata.get("source") or kind) or kind
        return {
            "kind": kind,
            "status": str(record.get("status") or "pending").strip().lower(),
            "category": str(record.get("category") or "uncategorized"),
            "tool": tool,
            "connector": connector,
            "workspace": workspace,
            "risk": risk,
            "source": source,
            "created_at": _parse(record.get("created_at")),
            "decided_at": _parse(record.get("decided_at")),
            "deferred_until": _parse(record.get("deferred_until")),
            "decisions": decisions,
            "audit_events": audit_events,
            "has_plan": bool(record.get("plan_id")),
        }

    # -- metric groups ----------------------------------------------------

    @staticmethod
    def _volume(items: Sequence[Mapping[str, Any]]) -> dict[str, int]:
        by_status: dict[str, int] = {}
        pending_approvals = 0
        for item in items:
            by_status[item["status"]] = by_status.get(item["status"], 0) + 1
            if item["status"] == "pending" and item["kind"] == "approval":
                pending_approvals += 1

        def outcome_count(status: str) -> int:
            return sum(
                1
                for item in items
                if item["status"] == status or status in item.get("decisions", set())
            )

        return {
            "created_total": len(items),
            "pending_total": by_status.get("pending", 0),
            "approved_total": outcome_count("approved"),
            "rejected_total": outcome_count("rejected"),
            "deferred_total": outcome_count("deferred"),
            "expired_total": outcome_count("expired"),
            "recovery_required_total": outcome_count("recovery_required"),
            "pending_approvals": pending_approvals,
        }

    def _times(self, items: Sequence[Mapping[str, Any]], *, now: datetime) -> dict[str, float]:
        decision_secs: list[float] = []
        deferred_secs: list[float] = []
        oldest_pending = 0.0
        for item in items:
            created = item["created_at"]
            decided = item["decided_at"]
            was_decided = item["status"] in _DECIDED or bool(
                set(item.get("decisions", set())) & _DECIDED
            )
            if was_decided and created is not None and decided is not None and decided >= created:
                decision_secs.append((decided - created).total_seconds())
            if item["status"] == "deferred" and item["deferred_until"] is not None:
                anchor = decided or created
                if anchor is not None and item["deferred_until"] >= anchor:
                    deferred_secs.append((item["deferred_until"] - anchor).total_seconds())
            deferred_started: datetime | None = None
            for event in item.get("audit_events", []):
                event_status = str(event.get("new_status") or "").strip().lower()
                event_time = _parse(event.get("timestamp"))
                if event_status == "deferred" and event_time is not None:
                    deferred_started = event_time
                elif event_status in {"approved", "rejected"} and deferred_started is not None and event_time is not None:
                    if event_time >= deferred_started:
                        deferred_secs.append((event_time - deferred_started).total_seconds())
                    deferred_started = None
            if item["status"] == "pending" and created is not None:
                oldest_pending = max(oldest_pending, (now - created).total_seconds())
        decision_secs.sort()
        return {
            "average_decision_time": _mean(decision_secs),
            "median_decision_time": _percentile(decision_secs, 0.5),
            "p95_decision_time": _percentile(decision_secs, 0.95),
            "oldest_pending_age": oldest_pending,
            "average_deferred_duration": _mean(deferred_secs),
        }

    @staticmethod
    def _quality(items: Sequence[Mapping[str, Any]]) -> dict[str, float]:
        def count(status: str) -> int:
            return sum(
                1
                for item in items
                if item["status"] == status or status in item.get("decisions", set())
            )

        approved = count("approved")
        rejected = count("rejected")
        deferred = count("deferred")
        decided = approved + rejected + deferred
        rate = (lambda n: round(n / decided, 4) if decided else 0.0)
        return {
            "approval_rate": rate(approved),
            "rejection_rate": rate(rejected),
            "defer_rate": rate(deferred),
        }

    @staticmethod
    def _segment(items: Sequence[Mapping[str, Any]], dimension: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in items:
            key = str(_scrub(str(item.get(dimension) or "unknown")))
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))

    @staticmethod
    def _time_segment(items: Sequence[Mapping[str, Any]], *, now: datetime) -> dict[str, int]:
        counts = {"last_24h": 0, "days_2_to_7": 0, "days_8_to_30": 0, "older": 0}
        for item in items:
            created = item.get("created_at")
            if created is None:
                continue
            age = max(timedelta(0), now - created)
            if age <= timedelta(days=1):
                counts["last_24h"] += 1
            elif age <= timedelta(days=7):
                counts["days_2_to_7"] += 1
            elif age <= timedelta(days=30):
                counts["days_8_to_30"] += 1
            else:
                counts["older"] += 1
        return counts

    @staticmethod
    def _window_volume(items: Sequence[Mapping[str, Any]], *, now: datetime, days: int) -> dict[str, int]:
        threshold = now - timedelta(days=days)
        created = 0
        decided = 0
        for item in items:
            if item["created_at"] is not None and item["created_at"] >= threshold:
                created += 1
            if item["decided_at"] is not None and item["decided_at"] >= threshold:
                decided += 1
        return {"created": created, "decided": decided}

    def _critical_pending(self, now: datetime) -> int:
        critical = {"delete_request", "connector_permission_change", "credential_change", "sensitive_document"}
        count = 0
        for item in self._items(window_days=None, now=now):
            if item["status"] == "recovery_required":
                count += 1
                continue
            if item["status"] != "pending":
                continue
            if item["category"] in critical or item["risk"] in {"critical", "destructive"}:
                count += 1
        return count

    def _overdue_pending(self, now: datetime, *, overdue_hours: int = 4) -> int:
        threshold = timedelta(hours=overdue_hours).total_seconds()
        count = 0
        for item in self._items(window_days=None, now=now):
            created = item["created_at"]
            if item["status"] == "pending" and created is not None and (now - created).total_seconds() >= threshold:
                count += 1
            elif (
                item["status"] == "deferred"
                and item.get("deferred_until") is not None
                and item["deferred_until"] <= now
            ):
                count += 1
            elif item["status"] == "recovery_required":
                count += 1
        return count

    # -- audit counters ---------------------------------------------------

    def _audit_metrics(
        self,
        items: Sequence[Mapping[str, Any]],
    ) -> tuple[dict[str, int], dict[str, float]]:
        security = {
            "blocked_unsafe_execution_count": 0,
            "duplicate_execution_prevented_count": 0,
            "stale_decision_conflict_count": 0,
            "secret_redaction_count": 0,
            "privacy_block_count": 0,
            "workspace_mismatch_count": 0,
        }
        resume_successes = sum(
            1
            for item in items
            if item.get("kind") == "approval"
            and item.get("has_plan")
            and item.get("status") in {"executed", "completed"}
        )
        resume_failures = sum(
            1
            for item in items
            if item.get("kind") == "approval"
            and item.get("has_plan")
            and item.get("status") == "failed"
        )
        reopened = 0

        paths = (
            "memory_governance_audit.jsonl",
            "action_audit.jsonl",
            "review_approval_audit.jsonl",
            "approval_recovery_audit.jsonl",
        )
        fields = (
            "event", "type", "status", "decision", "reason", "error",
            "result", "command", "action", "note", "old_status", "new_status",
        )
        for name in paths:
            rows, _ = self._read_jsonl(self._native_path(name))
            for row in rows:
                text = " ".join(str(row.get(field) or "").lower() for field in fields)
                status = str(row.get("status") or row.get("decision") or row.get("result") or "").lower()
                if status in {"blocked", "rejected", "denied", "approval_required"}:
                    security["blocked_unsafe_execution_count"] += 1
                duplicate_tokens = (
                    "duplicate_execution", "already_consumed", "duplicate", "execution_in_progress",
                )
                if any(token in text for token in duplicate_tokens):
                    security["duplicate_execution_prevented_count"] += 1
                if any(token in text for token in ("version_conflict", "stale_decision", "stale_version")):
                    security["stale_decision_conflict_count"] += 1
                redaction_tokens = (
                    "secret_blocked", "credential_blocked", "secret_redacted", "redaction",
                )
                if any(token in text for token in redaction_tokens):
                    security["secret_redaction_count"] += 1
                if any(token in text for token in ("privacy_mode", "privacy_block")):
                    security["privacy_block_count"] += 1
                if any(token in text for token in ("workspace_mismatch", "wrong_workspace", "binding_workspace")):
                    security["workspace_mismatch_count"] += 1
                if "resume" in text and status in {"completed", "executed", "success", "ok"}:
                    resume_successes += 1
                if "resume" in text and status in {"error", "failed", "failure"}:
                    resume_failures += 1
                if "reopen" in text:
                    reopened += 1

        for item in items:
            for event in item.get("audit_events", []):
                old_status = str(event.get("old_status") or "").lower()
                new_status = str(event.get("new_status") or "").lower()
                if old_status in {"approved", "rejected", "completed", "expired"} and new_status == "pending":
                    reopened += 1

        resume_total = resume_successes + resume_failures
        resolved = sum(
            1
            for item in items
            if item.get("status") in {"approved", "rejected", "executed", "completed", "expired"}
            or bool(set(item.get("decisions", set())) & {"approved", "rejected"})
        )
        operational_quality = {
            "resume_success_count": float(resume_successes),
            "resume_failure_count": float(resume_failures),
            "review_reopen_count": float(reopened),
            "resume_success_rate": round(resume_successes / resume_total, 4) if resume_total else 0.0,
            "resume_failure_rate": round(resume_failures / resume_total, 4) if resume_total else 0.0,
            "review_reopen_rate": round(min(reopened / resolved, 1.0), 4) if resolved else 0.0,
        }
        return security, operational_quality

    # -- io ---------------------------------------------------------------

    def _native_path(self, name: str) -> Path:
        return self.project_root / "runtime" / "native" / name

    def _read_jsonl(self, path: Path) -> tuple[list[dict[str, Any]], int]:
        rows: list[dict[str, Any]] = []
        corrupted = 0
        if not path.exists():
            return rows, corrupted
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return rows, corrupted
        for line in lines:
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                corrupted += 1
                self._corrupted += 1
                continue
            if isinstance(parsed, dict):
                rows.append(parsed)
            else:
                corrupted += 1
                self._corrupted += 1
        return rows, corrupted


def _mean(values: Sequence[float]) -> float:
    return round(sum(values) / len(values), 3) if values else 0.0


def _scrub(value: Any) -> Any:
    """Redact secret-looking strings anywhere in the export."""

    if isinstance(value, str):
        result = _SECRET_GUARD.inspect_memory_write(value)
        if result.reason == "secret_redacted" and result.decision != PrivacyDecision.ALLOW:
            return result.redacted_text or "[REDACTED_SECRET]"
        return value
    if isinstance(value, Mapping):
        return {key: _scrub(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_scrub(item) for item in value)
    return value
