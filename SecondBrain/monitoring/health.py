"""Health monitoring with a traffic-light (Ampel) status per component.

Aggregates 12 components: CPU, RAM, Disk, GPU, DB, Queue, Agents, Connectors,
Memory, Embedding, Provider, Audit. Every check is defensive - it never raises;
if the underlying service is not reachable in the current environment the check
reports ``unavailable`` (grey) with a reason, so the same monitor runs in a bare
sandbox and on a fully provisioned machine.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable

try:
    import psutil

    _HAS_PSUTIL = True
except Exception:  # noqa: BLE001
    psutil = None  # type: ignore
    _HAS_PSUTIL = False

__all__ = ["HealthStatus", "AMPEL", "HealthCheck", "HealthMonitor", "DEFAULT_THRESHOLDS"]


class HealthStatus(StrEnum):
    OK = "ok"
    WARN = "warn"
    CRITICAL = "critical"
    UNAVAILABLE = "unavailable"


AMPEL = {
    HealthStatus.OK: "green",
    HealthStatus.WARN: "yellow",
    HealthStatus.CRITICAL: "red",
    HealthStatus.UNAVAILABLE: "grey",
}

# Order used to compute the overall status (worst wins; unavailable is neutral).
_SEVERITY = {HealthStatus.OK: 0, HealthStatus.WARN: 1, HealthStatus.CRITICAL: 2}

DEFAULT_THRESHOLDS: dict[str, dict[str, float]] = {
    "cpu": {"warn": 80.0, "critical": 95.0},
    "ram": {"warn": 85.0, "critical": 95.0},
    "disk": {"warn": 85.0, "critical": 95.0},
    "queue": {"warn": 25.0, "critical": 100.0},
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class HealthCheck:
    component: str
    status: HealthStatus
    value: Any = ""
    detail: str = ""
    metrics: dict[str, float] = field(default_factory=dict)

    @property
    def ampel(self) -> str:
        return AMPEL[self.status]

    def to_dict(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "status": self.status.value,
            "ampel": self.ampel,
            "value": self.value,
            "detail": self.detail,
            "metrics": dict(self.metrics),
        }


def _by_threshold(component: str, pct: float, thresholds: dict[str, dict[str, float]]) -> HealthStatus:
    t = thresholds.get(component, {})
    if pct >= t.get("critical", 95.0):
        return HealthStatus.CRITICAL
    if pct >= t.get("warn", 85.0):
        return HealthStatus.WARN
    return HealthStatus.OK


class HealthMonitor:
    def __init__(self, project_root: str | Path = ".", *, thresholds: dict[str, dict[str, float]] | None = None) -> None:
        self.root = Path(project_root).resolve()
        self.thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}

    # -- orchestration ----------------------------------------------------

    def checks(self) -> list[HealthCheck]:
        order: list[tuple[str, Callable[[], HealthCheck]]] = [
            ("CPU", self._cpu),
            ("RAM", self._ram),
            ("Disk", self._disk),
            ("GPU", self._gpu),
            ("DB", self._db),
            ("Queue", self._queue),
            ("Agenten", self._agents),
            ("Connectoren", self._connectors),
            ("Memory", self._memory),
            ("Embedding", self._embedding),
            ("Provider", self._provider),
            ("Audit", self._audit),
        ]
        out: list[HealthCheck] = []
        for name, fn in order:
            try:
                out.append(fn())
            except Exception as exc:  # noqa: BLE001 - a broken check degrades, never crashes
                out.append(HealthCheck(name, HealthStatus.UNAVAILABLE, detail=f"{type(exc).__name__}: {exc}"))
        return out

    def snapshot(self) -> dict[str, Any]:
        checks = self.checks()
        overall = self._overall(checks)
        counts = {s.value: sum(1 for c in checks if c.status == s) for s in HealthStatus}
        return {
            "schema": "secondbrain.monitoring.health.v1",
            "timestamp": _utc_now(),
            "overall": overall.value,
            "ampel": AMPEL[overall],
            "counts": counts,
            "checks": [c.to_dict() for c in checks],
        }

    @staticmethod
    def _overall(checks: list[HealthCheck]) -> HealthStatus:
        graded = [c.status for c in checks if c.status in _SEVERITY]
        if not graded:
            return HealthStatus.UNAVAILABLE
        return max(graded, key=lambda s: _SEVERITY[s])

    # -- system checks (real via psutil) ----------------------------------

    def _cpu(self) -> HealthCheck:
        if not _HAS_PSUTIL:
            return HealthCheck("CPU", HealthStatus.UNAVAILABLE, detail="psutil nicht installiert")
        pct = float(psutil.cpu_percent(interval=0.15))
        return HealthCheck("CPU", _by_threshold("cpu", pct, self.thresholds), value=f"{pct:g}%", metrics={"percent": pct})

    def _ram(self) -> HealthCheck:
        if not _HAS_PSUTIL:
            return HealthCheck("RAM", HealthStatus.UNAVAILABLE, detail="psutil nicht installiert")
        vm = psutil.virtual_memory()
        pct = float(vm.percent)
        return HealthCheck("RAM", _by_threshold("ram", pct, self.thresholds), value=f"{pct:g}%",
                           metrics={"percent": pct, "used_gb": round(vm.used / 1e9, 2), "total_gb": round(vm.total / 1e9, 2)})

    def _disk(self) -> HealthCheck:
        if not _HAS_PSUTIL:
            return HealthCheck("Disk", HealthStatus.UNAVAILABLE, detail="psutil nicht installiert")
        try:
            du = psutil.disk_usage(str(self.root))
        except Exception:  # noqa: BLE001
            du = psutil.disk_usage("/")
        pct = float(du.percent)
        return HealthCheck("Disk", _by_threshold("disk", pct, self.thresholds), value=f"{pct:g}%",
                           metrics={"percent": pct, "free_gb": round(du.free / 1e9, 2), "total_gb": round(du.total / 1e9, 2)})

    def _gpu(self) -> HealthCheck:
        try:
            import pynvml  # type: ignore

            pynvml.nvmlInit()
            count = pynvml.nvmlDeviceGetCount()
            if count == 0:
                return HealthCheck("GPU", HealthStatus.UNAVAILABLE, detail="keine GPU erkannt")
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            util = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
            return HealthCheck("GPU", HealthStatus.OK, value=f"{util}%", metrics={"utilization": float(util), "devices": float(count)})
        except Exception:  # noqa: BLE001
            return HealthCheck("GPU", HealthStatus.UNAVAILABLE, detail="pynvml/NVIDIA nicht verfuegbar")

    # -- application checks (best effort, degrade gracefully) -------------

    def _db(self) -> HealthCheck:
        dsn = os.environ.get("DATABASE_URL") or os.environ.get("SECONDBRAIN_DATABASE_URL")
        if not dsn:
            return HealthCheck("DB", HealthStatus.UNAVAILABLE, detail="keine DATABASE_URL konfiguriert (SQLite/Dev)")
        try:
            from secondbrain.storage.db_executor import SqliteExecutor  # noqa: F401
            # A configured DSN is present; a real ping requires the driver on the host.
            return HealthCheck("DB", HealthStatus.OK, value="konfiguriert", detail="DATABASE_URL gesetzt")
        except Exception as exc:  # noqa: BLE001
            return HealthCheck("DB", HealthStatus.WARN, detail=f"kein Treiber: {type(exc).__name__}")

    def _queue(self) -> HealthCheck:
        try:
            from secondbrain.native.approval import NativeApprovalQueue

            pending = len(NativeApprovalQueue(self.root).list(status="pending"))
            status = _by_threshold("queue", float(pending), self.thresholds)
            return HealthCheck("Queue", status, value=f"{pending} offen", metrics={"pending": float(pending)})
        except Exception as exc:  # noqa: BLE001
            return HealthCheck("Queue", HealthStatus.UNAVAILABLE, detail=f"{type(exc).__name__}")

    def _agents(self) -> HealthCheck:
        runtime = self.root / "runtime" / "swarm_v124" / "agents.json"
        try:
            if runtime.exists():
                import json

                data = json.loads(runtime.read_text(encoding="utf-8"))
                n = len(data) if isinstance(data, list) else 0
                return HealthCheck("Agenten", HealthStatus.OK, value=f"{n} registriert", metrics={"agents": float(n)})
            from dataclasses import asdict  # noqa: F401
            from secondbrain.swarm.registry import DEFAULT_AGENTS

            n = len(DEFAULT_AGENTS)
            return HealthCheck("Agenten", HealthStatus.OK, value=f"{n} (default)", metrics={"agents": float(n)})
        except Exception as exc:  # noqa: BLE001
            return HealthCheck("Agenten", HealthStatus.UNAVAILABLE, detail=f"{type(exc).__name__}")

    def _connectors(self) -> HealthCheck:
        try:
            from secondbrain.connector_runtime.center import ConnectorCenter  # type: ignore  # noqa: F401

            return HealthCheck("Connectoren", HealthStatus.OK, value="Runtime geladen")
        except Exception:  # noqa: BLE001
            return HealthCheck("Connectoren", HealthStatus.UNAVAILABLE, detail="Connector-Runtime/Credentials nicht verfuegbar")

    def _memory(self) -> HealthCheck:
        try:
            from secondbrain.agent.memory import InMemoryMemoryStore  # noqa: F401

            return HealthCheck("Memory", HealthStatus.OK, value="Store verfuegbar")
        except Exception as exc:  # noqa: BLE001
            return HealthCheck("Memory", HealthStatus.UNAVAILABLE, detail=f"{type(exc).__name__}")

    def _embedding(self) -> HealthCheck:
        provider = os.environ.get("SECONDBRAIN_EMBEDDING_PROVIDER", "")
        if not provider:
            return HealthCheck("Embedding", HealthStatus.UNAVAILABLE, detail="kein Embedding-Provider konfiguriert")
        return HealthCheck("Embedding", HealthStatus.OK, value=provider)

    def _provider(self) -> HealthCheck:
        keys = {"OpenAI": "OPENAI_API_KEY", "Ollama": "OLLAMA_HOST", "Gemini": "GEMINI_API_KEY"}
        present = [name for name, env in keys.items() if os.environ.get(env)]
        if not present:
            return HealthCheck("Provider", HealthStatus.UNAVAILABLE, detail="kein LLM-Provider konfiguriert")
        return HealthCheck("Provider", HealthStatus.OK, value=", ".join(present), metrics={"providers": float(len(present))})

    def _audit(self) -> HealthCheck:
        candidates = [
            self.root / "runtime" / "native" / "action_audit.jsonl",
            self.root / "runtime" / "native" / "memory_governance_audit.jsonl",
        ]
        found = [p for p in candidates if p.exists()]
        if not found:
            return HealthCheck("Audit", HealthStatus.UNAVAILABLE, detail="kein Audit-Log vorhanden")
        lines = 0
        for p in found:
            try:
                lines += sum(1 for line in p.read_text(encoding="utf-8").splitlines() if line.strip())
            except OSError:
                pass
        return HealthCheck("Audit", HealthStatus.OK, value=f"{lines} Eintraege", metrics={"entries": float(lines)})
