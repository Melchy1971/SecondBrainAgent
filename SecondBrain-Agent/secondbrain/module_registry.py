from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib import import_module
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModuleDescriptor:
    key: str
    title: str
    capability: str
    import_path: str | None = None
    launcher_class: str | None = None
    status_method: str | None = None
    command_prefixes: tuple[str, ...] = ()
    commands: tuple[str, ...] = ()
    critical: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["command_prefixes"] = list(self.command_prefixes)
        data["commands"] = list(self.commands)
        return data


DEFAULT_MODULES: tuple[ModuleDescriptor, ...] = (
    ModuleDescriptor(
        "core",
        "Core Runtime",
        "runtime",
        "secondbrain.launcher_runtime_v126",
        "SecondBrainLauncherV126",
        "core126_status",
        ("core-", "status", "health", "p1-"),
        ("core-status", "status", "health", "modules", "module-status", "module-health", "p0-doctor", "p0-gate", "p0-report", "p0-smoke", "p0-contract", "p0-readiness", "p0-bootstrap", "p0-production", "p0-audit", "p1-rag-status", "p1-rag-ingest-text", "p1-rag-ingest-file", "p1-rag-search", "p1-rag-vector-search", "p1-rag-hybrid-search", "p1-rag-answer", "p1-rag-sources", "p1-rag-explain", "p1-rag-validate", "p1-rag-quality", "p1-rag-reindex", "p1-embedding-status", "p1-retrieval-benchmark", "p1-retrieval-metrics", "p1-production", "p1-gate", "command-index"),
        True,
    ),
    ModuleDescriptor(
        "desktop",
        "Desktop OS",
        "desktop",
        "secondbrain.launcher_runtime_v125",
        "SecondBrainLauncherV125",
        "desktop_status",
        ("desktop-",),
        (
            "desktop-status",
            "desktop-open",
            "desktop-dashboard",
            "desktop-activity",
            "desktop-widgets",
            "desktop-widget-enable",
            "desktop-commands",
            "desktop-search-command",
            "desktop-command",
            "desktop-notify",
            "desktop-notifications",
            "desktop-session",
        ),
        True,
    ),
    ModuleDescriptor(
        "voice",
        "Realtime Voice",
        "voice",
        "secondbrain.launcher_runtime_v126",
        "SecondBrainLauncherV126",
        "voice_status_v126",
        ("voice-",),
        (
            "voice-status2",
            "voice-session2",
            "voice-sessions2",
            "voice-wake",
            "voice-transcribe",
            "voice-parse2",
            "voice-handle2",
            "voice-speak2",
            "voice-interrupt",
            "voice-events",
            "voice-memory",
        ),
        False,
    ),
    ModuleDescriptor(
        "graph",
        "Knowledge Graph",
        "graph",
        "secondbrain.launcher_runtime_v123",
        "SecondBrainLauncherV123",
        "graph_status",
        ("graph-",),
        (
            "graph-status",
            "graph-ingest-text",
            "graph-ingest-file",
            "graph-search",
            "graph-neighbors",
            "graph-timeline",
            "graph-contradictions",
            "graph-export",
        ),
        False,
    ),
    ModuleDescriptor(
        "mobile",
        "Mobile Companion",
        "mobile",
        "secondbrain.mobile_companion",
        "MobileCompanionRuntime",
        "status",
        ("mobile16-",),
        (
            "mobile16-migrate",
            "mobile16-status",
            "mobile16-manifest",
            "mobile16-pair-request",
            "mobile16-pair-approve",
            "mobile16-pairing-requests",
            "mobile16-devices",
            "mobile16-capture",
            "mobile16-voice-note",
            "mobile16-camera-ocr",
            "mobile16-offline-queue",
            "mobile16-offline-replay",
            "mobile16-push",
            "mobile16-push-outbox",
            "mobile16-push-deliver",
            "mobile16-widgets",
            "mobile16-widget-enable",
            "mobile16-sync",
            "mobile16-sync-runs",
            "mobile16-session-create",
            "mobile16-sessions",
        ),
        False,
    ),
)


class ModuleRegistry:
    def __init__(self, modules: tuple[ModuleDescriptor, ...] = DEFAULT_MODULES):
        self._modules = {m.key: m for m in modules}

    def list(self) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self._modules.values()]

    def keys(self) -> list[str]:
        return list(self._modules.keys())

    def get(self, key: str) -> ModuleDescriptor:
        return self._modules[key]

    def has(self, key: str) -> bool:
        return key in self._modules

    def command_index(self) -> dict[str, str]:
        return {command: module.key for module in self._modules.values() for command in module.commands}

    def command_conflicts(self) -> list[dict[str, Any]]:
        owners: dict[str, list[str]] = {}
        for module in self._modules.values():
            for command in module.commands:
                owners.setdefault(command, []).append(module.key)
        return [
            {"command": command, "modules": modules}
            for command, modules in sorted(owners.items())
            if len(modules) > 1
        ]

    def critical_modules(self) -> list[dict[str, Any]]:
        return [module.to_dict() for module in self._modules.values() if module.critical]

    def resolve_command(self, command: str | None) -> ModuleDescriptor | None:
        if not command:
            return self._modules["core"]
        if command in self._modules:
            return self._modules[command]
        index = self.command_index()
        if command in index:
            return self._modules[index[command]]
        for module in self._modules.values():
            if any(command == prefix.rstrip("-") or command.startswith(prefix) for prefix in module.command_prefixes):
                return module
        return None

    def import_health(self) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        ok = True
        for module in self._modules.values():
            status = "skipped"
            error = None
            if module.import_path:
                try:
                    import_module(module.import_path)
                    status = "ok"
                except Exception as exc:  # pragma: no cover - defensive boundary
                    status = "error"
                    error = str(exc)
                    if module.critical:
                        ok = False
            checks.append({"key": module.key, "title": module.title, "critical": module.critical, "status": status, "error": error})
        return {"ok": ok, "modules": checks}

    def runtime_health(self, project_root: str | Path, profile: str | None = None) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        ok = True
        for module in self._modules.values():
            if not (module.import_path and module.launcher_class and module.status_method):
                checks.append({"key": module.key, "status": "skipped", "critical": module.critical})
                continue
            try:
                imported = import_module(module.import_path)
                cls = getattr(imported, module.launcher_class)
                if module.key == "mobile":
                    runtime = cls(project_root)
                else:
                    runtime = cls(project_root, profile)
                status_obj = getattr(runtime, module.status_method)()
                checks.append({"key": module.key, "title": module.title, "critical": module.critical, "status": "ok", "summary": _summarize_status(status_obj)})
            except Exception as exc:  # pragma: no cover - integration boundary
                checks.append({"key": module.key, "title": module.title, "critical": module.critical, "status": "error", "error": str(exc)})
                if module.critical:
                    ok = False
        return {"ok": ok, "modules": checks}


def _summarize_status(value: Any) -> Any:
    if isinstance(value, dict):
        keep = {k: v for k, v in value.items() if k in {"status", "version", "runtime_dir", "services", "widgets", "sessions", "devices", "events", "state"}}
        return keep or {"keys": sorted(value.keys())[:12]}
    if isinstance(value, list):
        return {"count": len(value)}
    return value
