"""Unified operations monitoring (v30.99 delta).

Structured logging, the audit store, the health timeline, the performance
dashboard and runtime snapshots already exist. This module *connects* them into
one operational view: it runs component checks with a real timeout, isolates a
failing check so one broken module never blanks the dashboard, maps the existing
traffic-light ``HealthStatus`` onto the six operational states, records history,
supports acknowledge and a maintenance mode that suppresses expected warnings
traceably, generates alerts from status, and exports a secret-free snapshot.

It builds no new storage: history uses the existing ``HealthTimeline`` and
redaction the existing ``RedactionMiddleware`` when available (both injectable so
the aggregation logic is testable in isolation).
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from time import perf_counter
from typing import Any, Callable, Mapping, Sequence
from uuid import uuid4

__all__ = [
    "OperationalStatus", "HealthCheckResult", "OperationsMonitor",
    "map_health_status", "worst_status",
]


class OperationalStatus(StrEnum):
    READY = "ready"
    DEGRADED = "degraded"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    RECOVERING = "recovering"
    MAINTENANCE = "maintenance"


# Severity for worst-state; UNAVAILABLE/MAINTENANCE/RECOVERING are neutral for
# the overall grade (they do not upgrade a healthy system, nor mask a blocker).
_SEVERITY = {
    OperationalStatus.READY: 0,
    OperationalStatus.RECOVERING: 1,
    OperationalStatus.DEGRADED: 2,
    OperationalStatus.BLOCKED: 3,
}
_NEUTRAL = {OperationalStatus.UNAVAILABLE, OperationalStatus.MAINTENANCE}

# Map the existing traffic-light HealthStatus values onto operational states.
_TRAFFIC_MAP = {
    "ok": OperationalStatus.READY,
    "green": OperationalStatus.READY,
    "warn": OperationalStatus.DEGRADED,
    "yellow": OperationalStatus.DEGRADED,
    "critical": OperationalStatus.BLOCKED,
    "red": OperationalStatus.BLOCKED,
    "unavailable": OperationalStatus.UNAVAILABLE,
    "grey": OperationalStatus.UNAVAILABLE,
}
_SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|passwd|bearer|dsn|postgres://|sk-[A-Za-z0-9]{6,}|-----BEGIN)"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def map_health_status(value: str | OperationalStatus) -> OperationalStatus:
    if isinstance(value, OperationalStatus):
        return value
    return _TRAFFIC_MAP.get(str(value).strip().lower(), OperationalStatus.UNAVAILABLE)


def worst_status(results: Sequence["HealthCheckResult"]) -> OperationalStatus:
    graded = [r.status for r in results if r.status not in _NEUTRAL]
    if not graded:
        return OperationalStatus.UNAVAILABLE if results else OperationalStatus.READY
    return max(graded, key=lambda s: _SEVERITY[s])


def _scrub(value: Any) -> Any:
    """Remove secret-looking content from any exported value."""
    if isinstance(value, Mapping):
        return {k: ("***" if _SECRET_RE.search(str(k)) else _scrub(v)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_scrub(v) for v in value]
    if isinstance(value, str):
        return _SECRET_RE.sub("[REDACTED]", value)
    return value


@dataclass
class HealthCheckResult:
    component: str
    status: OperationalStatus
    checked_at: str = field(default_factory=_now)
    latency_ms: float = 0.0
    message: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    remediation: str = ""
    correlation_id: str = field(default_factory=lambda: uuid4().hex)
    # detailed diagnostics stay OUT of the main view (support center only)
    diagnostics: str = ""

    def public_dict(self) -> dict[str, Any]:
        """Main-view representation: no stacktrace, no secrets, no technical id
        beyond the correlation id needed for support drill-down."""
        return {
            "component": self.component,
            "status": self.status.value,
            "checked_at": self.checked_at,
            "latency_ms": round(self.latency_ms, 2),
            "message": _SECRET_RE.sub("[REDACTED]", self.message),
            "metrics": _scrub(self.metrics),
            "blockers": self.blockers,
            "warnings": self.warnings,
            "remediation": self.remediation,
            "correlation_id": self.correlation_id,
        }

    def export_dict(self) -> dict[str, Any]:
        data = self.public_dict()
        return data  # already secret-scrubbed; diagnostics deliberately omitted


class OperationsMonitor:
    def __init__(self, checks: Mapping[str, Callable[[], Mapping[str, Any]]], *,
                 timeline: Any | None = None, redactor: Any | None = None,
                 default_timeout_s: float = 5.0) -> None:
        self._checks = dict(checks)
        self._timeout = default_timeout_s
        self._maintenance: set[str] = set()
        self._acknowledged: set[str] = set()
        self._previous: dict[str, OperationalStatus] = {}
        self._timeline = timeline  # optional existing HealthTimeline
        self._redactor = redactor  # optional existing RedactionMiddleware

    # -- configuration ----------------------------------------------------

    def set_maintenance(self, component: str, on: bool = True) -> None:
        (self._maintenance.add if on else self._maintenance.discard)(component)

    def acknowledge(self, component: str) -> None:
        self._acknowledged.add(component)

    # -- evaluation -------------------------------------------------------

    def _run_one(self, component: str, fn: Callable[[], Mapping[str, Any]]) -> HealthCheckResult:
        start = perf_counter()
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                raw = pool.submit(fn).result(timeout=self._timeout)
        except FutureTimeout:
            return HealthCheckResult(component, OperationalStatus.UNAVAILABLE,
                                     latency_ms=(perf_counter() - start) * 1000.0,
                                     message="check_timeout", remediation="Prüfe Komponente / Timeout erhöhen",
                                     diagnostics="timeout")
        except Exception as exc:  # noqa: BLE001 - one broken check must not blank the board
            return HealthCheckResult(component, OperationalStatus.UNAVAILABLE,
                                     latency_ms=(perf_counter() - start) * 1000.0,
                                     message="check_error", remediation="Siehe Support Center",
                                     diagnostics=f"{type(exc).__name__}")
        latency = (perf_counter() - start) * 1000.0
        status = map_health_status(raw.get("status", "unavailable"))
        result = HealthCheckResult(
            component=component, status=status, latency_ms=latency,
            message=str(raw.get("message", "")), metrics=dict(raw.get("metrics", {})),
            blockers=list(raw.get("blockers", [])), warnings=list(raw.get("warnings", [])),
            remediation=str(raw.get("remediation", "")), diagnostics=str(raw.get("diagnostics", "")),
        )
        return result

    def evaluate(self) -> list[HealthCheckResult]:
        results: list[HealthCheckResult] = []
        for component, fn in self._checks.items():
            result = self._run_one(component, fn)
            # maintenance overlay: suppress warnings/blockers traceably
            if component in self._maintenance:
                result.warnings = []
                result.message = f"maintenance: {result.message}".strip()
                result.status = OperationalStatus.MAINTENANCE
            else:
                prev = self._previous.get(component)
                if prev in (OperationalStatus.BLOCKED, OperationalStatus.UNAVAILABLE) \
                        and result.status == OperationalStatus.READY:
                    result.status = OperationalStatus.RECOVERING
            self._previous[component] = result.status
            if self._timeline is not None:
                try:
                    self._timeline.record(component, result.status.value, detail=result.message)
                except Exception:  # noqa: BLE001 - history must never break monitoring
                    pass
            results.append(result)
        return results

    # -- views ------------------------------------------------------------

    def system_view(self) -> dict[str, Any]:
        results = self.evaluate()
        overall = worst_status(results)
        return {
            "overall": overall.value,
            "checked_at": _now(),
            "components": [r.public_dict() for r in results],
            "counts": {s.value: sum(1 for r in results if r.status == s) for s in OperationalStatus},
            "alerts": self.alerts(results),
        }

    def alerts(self, results: Sequence[HealthCheckResult]) -> list[dict[str, Any]]:
        out = []
        for r in results:
            if r.status in (OperationalStatus.BLOCKED, OperationalStatus.UNAVAILABLE) \
                    and r.component not in self._acknowledged and r.component not in self._maintenance:
                out.append({"component": r.component, "status": r.status.value,
                            "message": _SECRET_RE.sub("[REDACTED]", r.message),
                            "correlation_id": r.correlation_id})
        return out

    def export(self) -> dict[str, Any]:
        results = self.evaluate()
        payload = {
            "overall": worst_status(results).value,
            "generated_at": _now(),
            "components": [r.export_dict() for r in results],
        }
        if self._redactor is not None:
            try:
                return self._redactor.redact_payload(payload)
            except Exception:  # noqa: BLE001
                return _scrub(payload)
        return _scrub(payload)


def default_operations_monitor(project_root: str | Path = ".") -> OperationsMonitor:  # type: ignore[name-defined]
    """Wire the aggregator to the existing HealthMonitor + HealthTimeline.

    Lazy imports keep this module free of psutil/DB at import time.
    """
    from pathlib import Path as _P
    checks: dict[str, Callable[[], Mapping[str, Any]]] = {}
    timeline = None
    redactor = None
    try:
        from secondbrain.monitoring.health import HealthMonitor  # type: ignore
        monitor = HealthMonitor(str(project_root))
        for check in monitor.checks():
            checks[check.component] = (lambda c=check: {"status": c.status.value,
                                                        "message": str(c.detail or c.value),
                                                        "metrics": dict(c.metrics)})
    except Exception:  # noqa: BLE001
        pass
    try:
        from secondbrain.observability.health_timeline import HealthTimeline  # type: ignore
        timeline = HealthTimeline(str(project_root))
    except Exception:  # noqa: BLE001
        pass
    try:
        from secondbrain.observability.redaction import RedactionMiddleware  # type: ignore
        redactor = RedactionMiddleware()
    except Exception:  # noqa: BLE001
        pass
    return OperationsMonitor(checks, timeline=timeline, redactor=redactor)


from pathlib import Path  # noqa: E402  (kept at end so lazy default_* signature resolves)
