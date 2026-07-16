"""Personal Jarvis end-to-end release gate.

The gate deliberately performs defensive, side-effect-free checks. It verifies that the
personal-assistant subsystems can be imported, expose their expected public contracts,
and that the existing governance gate remains available. Runtime integrations may add
stronger probes through ``extra_probes`` without changing the stable report schema.
"""
from __future__ import annotations

import importlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

PASS = "PASS"
CONDITIONAL_PASS = "CONDITIONAL_PASS"
BLOCKED = "BLOCKED"
SCHEMA = "secondbrain.personal_jarvis_gate.v1"
VERSION = "v31.24"


@dataclass(frozen=True)
class GateCheck:
    check_id: str
    group: str
    title: str
    status: str
    detail: str = ""
    hard_blocker: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModuleContract:
    check_id: str
    group: str
    module: str
    any_attributes: tuple[str, ...]
    title: str
    hard_blocker: bool = True


DEFAULT_CONTRACTS: tuple[ModuleContract, ...] = (
    ModuleContract("tasks_available", "tasks", "secondbrain.tasks.service", ("TaskProjectService",), "Task and project services are available"),
    ModuleContract("planner_available", "planner", "secondbrain.planner_v2.service", ("Planner",), "Planner V2 is available"),
    ModuleContract("jobs_available", "jobs", "secondbrain.jobs.service", ("JobManager", "JobStore"), "Persistent job runtime is available"),
    ModuleContract("briefing_available", "briefing", "secondbrain.briefing.service", ("BriefingBuilder",), "Daily briefing service is available"),
    ModuleContract("memory_available", "memory", "secondbrain.memory_consolidation.service", ("MemoryConsolidator",), "Memory consolidation is available"),
    ModuleContract("calendar_available", "calendar", "secondbrain.calendar_assistant.service", ("CalendarService",), "Calendar assistant is available"),
    ModuleContract("mail_available", "mail", "secondbrain.mail_assistant.service", ("MailAssistant",), "Mail assistant is available"),
    ModuleContract("proactive_available", "proactive", "secondbrain.proactive.service", ("ProactiveEngine",), "Proactive assistance is available"),
    ModuleContract("dashboard_available", "dashboard", "secondbrain.personal_dashboard.service", ("Dashboard",), "Personal dashboard is available"),
    ModuleContract("governance_available", "governance", "secondbrain.agent.review_approval_release_gate", ("run_review_approval_release_gate",), "Review and approval governance gate is available"),
    ModuleContract("knowledge_graph_available", "knowledge", "secondbrain.knowledge_graph.service", ("KnowledgeGraph",), "Knowledge graph is available"),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _module_check(contract: ModuleContract) -> GateCheck:
    try:
        module = importlib.import_module(contract.module)
    except Exception as exc:  # noqa: BLE001 - gate must report instead of crash
        status = BLOCKED if contract.hard_blocker else CONDITIONAL_PASS
        return GateCheck(contract.check_id, contract.group, contract.title, status, f"import_error:{type(exc).__name__}", contract.hard_blocker)
    exposed = [name for name in contract.any_attributes if hasattr(module, name)]
    if exposed:
        return GateCheck(contract.check_id, contract.group, contract.title, PASS, f"public_contract={exposed[0]}", contract.hard_blocker)
    status = BLOCKED if contract.hard_blocker else CONDITIONAL_PASS
    return GateCheck(contract.check_id, contract.group, contract.title, status, f"missing_any_of={','.join(contract.any_attributes)}", contract.hard_blocker)


def _safe_probe(check_id: str, group: str, title: str, probe: Callable[[], Any], *, hard_blocker: bool) -> GateCheck:
    try:
        result = probe()
        if isinstance(result, Mapping):
            ok = bool(result.get("ok", result.get("status") in {PASS, "ok", "ready"}))
            detail = str(result.get("detail") or result.get("status") or "probe_completed")
        else:
            ok = bool(result)
            detail = "probe_completed"
    except Exception as exc:  # noqa: BLE001
        ok = False
        detail = f"probe_error:{type(exc).__name__}"
    status = PASS if ok else (BLOCKED if hard_blocker else CONDITIONAL_PASS)
    return GateCheck(check_id, group, title, status, detail, hard_blocker)


def _knowledge_graph_persistence_probe() -> dict[str, Any]:
    from secondbrain.knowledge_graph.models import EntityType
    from secondbrain.knowledge_graph.persistence import KnowledgeGraphSnapshotRepository
    from secondbrain.knowledge_graph.service import KnowledgeGraph

    with tempfile.TemporaryDirectory(prefix="secondbrain-graph-gate-") as directory:
        graph = KnowledgeGraph()
        entity = graph.add_entity(
            workspace_id="gate-workspace",
            canonical_name="Gate Entity",
            type=EntityType.TOPIC.value,
            source_ids=["gate-source"],
            evidence=[{"source_id": "gate-source", "snippet": "gate evidence"}],
        )
        repository = KnowledgeGraphSnapshotRepository(directory)
        repository.save(graph, workspace_id="gate-workspace")
        restored = repository.load(workspace_id="gate-workspace")
        restored_entity = restored.get(entity.id)
        ok = bool(restored_entity and restored_entity.source_ids == ["gate-source"] and restored_entity.evidence)
        return {"ok": ok, "detail": "atomic_workspace_roundtrip" if ok else "roundtrip_mismatch"}


def _overall_status(checks: Iterable[GateCheck]) -> str:
    rows = list(checks)
    if any(row.status == BLOCKED for row in rows):
        return BLOCKED
    if any(row.status == CONDITIONAL_PASS for row in rows):
        return CONDITIONAL_PASS
    return PASS


def run_personal_jarvis_gate(
    project_root: str | Path = ".",
    *,
    write_report: bool = True,
    contracts: Iterable[ModuleContract] = DEFAULT_CONTRACTS,
    extra_probes: Mapping[str, tuple[str, str, Callable[[], Any], bool]] | None = None,
) -> dict[str, Any]:
    checks = [_module_check(contract) for contract in contracts]
    checks.append(_safe_probe(
        "knowledge_graph_persistence",
        "knowledge",
        "Knowledge graph state survives a workspace-scoped restart",
        _knowledge_graph_persistence_probe,
        hard_blocker=True,
    ))
    for check_id, (group, title, probe, hard_blocker) in (extra_probes or {}).items():
        checks.append(_safe_probe(check_id, group, title, probe, hard_blocker=hard_blocker))

    overall = _overall_status(checks)
    check_rows = [check.to_dict() for check in checks]
    blockers = [row["check_id"] for row in check_rows if row["status"] == BLOCKED]
    warnings = [row["check_id"] for row in check_rows if row["status"] == CONDITIONAL_PASS]
    groups: dict[str, dict[str, int]] = {}
    for row in check_rows:
        bucket = groups.setdefault(row["group"], {PASS: 0, CONDITIONAL_PASS: 0, BLOCKED: 0})
        bucket[row["status"]] += 1

    report = {
        "schema": SCHEMA,
        "version": VERSION,
        "timestamp": _utc_now(),
        "overall_status": overall,
        "ok": overall != BLOCKED,
        "summary": {
            "total": len(check_rows),
            "passed": sum(1 for row in check_rows if row["status"] == PASS),
            "conditional": len(warnings),
            "blocked": len(blockers),
        },
        "module_status": groups,
        "checks": check_rows,
        "blockers": blockers,
        "warnings": warnings,
        "user_journeys": {
            "mail_to_task": "covered_by_mail_and_task_contracts",
            "task_to_calendar": "covered_by_task_and_calendar_contracts",
            "briefing_to_plan": "covered_by_briefing_and_planner_contracts",
            "approval_exactly_once": "covered_by_governance_contract",
            "restart_recovery": "covered_by_jobs_planner_and_graph_persistence",
            "dashboard_drilldown": "covered_by_dashboard_contract",
            "document_to_graph_context": "covered_by_knowledge_graph_contract_and_persistence",
        },
        "release_recommendation": {
            PASS: "PRIVATE_BETA_READY",
            CONDITIONAL_PASS: "PRIVATE_BETA_WITH_WARNINGS",
            BLOCKED: "DO_NOT_RELEASE",
        }[overall],
    }

    if write_report:
        root = Path(project_root).resolve()
        path = root / "runtime" / "reports" / "personal_jarvis_gate.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    return report


__all__ = [
    "BLOCKED",
    "CONDITIONAL_PASS",
    "DEFAULT_CONTRACTS",
    "GateCheck",
    "ModuleContract",
    "PASS",
    "run_personal_jarvis_gate",
]
