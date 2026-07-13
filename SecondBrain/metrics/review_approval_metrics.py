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
from bisect import bisect_left
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

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
    quality: dict[str, float]
    segments: dict[str, dict[str, int]]
    trends: dict[str, dict[str, int]]
    corrupted_audit_lines: int
    generated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "secondbrain.metrics.review_approval.v1",
            "generated_at": self.generated_at,
            "volume": dict(self.volume),
            "times": dict(self.times),
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
        if inbox is not None:
            self.approvals_records = list(inbox.approvals.list())
            self.reviews_records = list(inbox.reviews.list())
            self.project_root = Path(inbox.approvals.project_root)
        else:
            self.project_root = Path(project_root or Path.cwd()).resolve()
            self.approvals_records = self._read_jsonl(self._native_path("approval_queue.jsonl"))[0]
            self.reviews_records = self._read_jsonl(self._native_path("review_queue.jsonl"))[0]
        self._corrupted = 0

    # -- public -----------------------------------------------------------

    def compute(self, *, window_days: int | None = None) -> MetricsResult:
        now = self._now or _utc_now()
        self._corrupted = 0
        items = self._items(window_days=window_days, now=now)

        volume = self._volume(items)
        times = self._times(items, now=now)
        quality = self._quality(items)
        segments = {dim: self._segment(items, dim) for dim in _SEGMENT_DIMENSIONS}
        trends = {
            "7d": self._window_volume(items, now=now, days=7),
            "30d": self._window_volume(items, now=now, days=30),
        }
        # Audit-derived counters (tolerant of missing/corrupt files).
        quality.update(self._audit_counters())

        return MetricsResult(
            volume=volume,
            times=times,
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
        segments = result.segments["category"]
        most_common = max(segments.items(), key=lambda kv: kv[1])[0] if segments else ""
        return _scrub(
            {
                "open_approvals": result.volume["pending_approvals"],
                "critical_approvals": self._critical_pending(now),
                "overdue_reviews": self._overdue_pending(now),
                "average_decision_time": result.times["average_decision_time"],
                "blocked_unsafe_executions": result.quality.get("blocked_unsafe_execution_count", 0),
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
        workspace = str(record.get("workspace_id") or metadata.get("workspace_id") or "") or "unassigned"
        tool = str(record.get("tool_name") or record.get("command") or "") or "none"
        connector = str(
            record.get("connector")
            or metadata.get("connector")
            or payload.get("connector")
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
        return {
            "created_total": len(items),
            "pending_total": by_status.get("pending", 0),
            "approved_total": by_status.get("approved", 0),
            "rejected_total": by_status.get("rejected", 0),
            "deferred_total": by_status.get("deferred", 0),
            "expired_total": by_status.get("expired", 0),
            "pending_approvals": pending_approvals,
        }

    def _times(self, items: Sequence[Mapping[str, Any]], *, now: datetime) -> dict[str, float]:
        decision_secs: list[float] = []
        deferred_secs: list[float] = []
        oldest_pending = 0.0
        for item in items:
            created = item["created_at"]
            decided = item["decided_at"]
            if item["status"] in _DECIDED and created is not None and decided is not None and decided >= created:
                decision_secs.append((decided - created).total_seconds())
            if item["status"] == "deferred" and item["deferred_until"] is not None:
                anchor = decided or created
                if anchor is not None and item["deferred_until"] >= anchor:
                    deferred_secs.append((item["deferred_until"] - anchor).total_seconds())
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
        approved = sum(1 for item in items if item["status"] == "approved")
        rejected = sum(1 for item in items if item["status"] == "rejected")
        deferred = sum(1 for item in items if item["status"] == "deferred")
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
            key = str(item.get(dimension) or "unknown")
            counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))

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
        return count

    # -- audit counters ---------------------------------------------------

    def _audit_counters(self) -> dict[str, int]:
        duplicate = 0
        blocked = 0
        resume_failures = 0
        secret_redactions = 0

        gov_rows, _ = self._read_jsonl(self._native_path("memory_governance_audit.jsonl"))
        for row in gov_rows:
            decision = str(row.get("decision") or "")
            reason = str(row.get("reason") or "")
            if decision == "duplicate":
                duplicate += 1
            if decision == "blocked":
                blocked += 1
                if reason in {"secret_blocked", "credential_blocked"}:
                    secret_redactions += 1

        action_rows, _ = self._read_jsonl(self._native_path("action_audit.jsonl"))
        for row in action_rows:
            status = str(row.get("status") or "")
            if status in {"blocked", "rejected"}:
                blocked += 1
            if "resume" in str(row.get("command") or "").lower() and status in {"error", "failed"}:
                resume_failures += 1

        return {
            "duplicate_prevention_count": duplicate,
            "blocked_unsafe_execution_count": blocked,
            "resume_failure_count": resume_failures,
            "secret_redaction_count": secret_redactions,
        }

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
