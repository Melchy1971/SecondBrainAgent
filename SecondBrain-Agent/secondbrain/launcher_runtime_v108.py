from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import argparse
import json
import os
import platform
import subprocess
import sys
import time

from .ai_runtime_v105 import load_model_router
from .connector_runtime_v104 import registry_from_config, sync_all
from .desktop_commands_v106 import DesktopCommandService
from .runtime_events_v104 import JsonlEventStore, RuntimeEvent
from .secure_agent_kernel_v107 import SecureAgentKernel
from .advanced_rag_v109 import AdvancedRagIndex
from .autonomous_agent_v110 import AutonomousAgentRuntime, ToolHost, run_to_summary


@dataclass
class ServiceStatus:
    name: str
    enabled: bool
    status: str
    detail: str = ""


@dataclass
class LauncherConfig:
    project_root: Path
    vault_path: Path
    runtime_dir: Path
    events_dir: Path
    profile: str
    services: dict[str, bool]
    default_provider: str = "echo"

    @classmethod
    def default(cls, project_root: Path) -> "LauncherConfig":
        return cls(
            project_root=project_root,
            vault_path=project_root.parent / "SecondBrain",
            runtime_dir=project_root / "runtime",
            events_dir=project_root / "events" / "runtime",
            profile="safe",
            services={
                "event_store": True,
                "connectors": True,
                "ai_runtime": True,
                "agent_kernel": True,
                "desktop_commands": True,
                "security": True,
                "autonomous_agent": True,
                "api_server": False,
                "gui": False,
                "voice": False,
            },
            default_provider="echo",
        )


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.lower() in {"true", "yes", "on"}:
        return True
    if value.lower() in {"false", "no", "off"}:
        return False
    if value.lower() in {"null", "none"}:
        return None
    try:
        return int(value)
    except ValueError:
        return value.strip('"\'')


def load_runtime_yaml(path: Path) -> dict[str, Any]:
    """Tiny YAML reader for the simple runtime config used here. Avoids hard PyYAML dependency."""
    if not path.exists():
        return {}
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        line = raw.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value == "":
            node: dict[str, Any] = {}
            parent[key] = node
            stack.append((indent, node))
        else:
            parent[key] = _parse_scalar(value)
    return root


def load_launcher_config(project_root: Path, profile: str | None = None) -> LauncherConfig:
    cfg = LauncherConfig.default(project_root)
    raw = load_runtime_yaml(project_root / "config" / "runtime.yaml")
    runtime = raw.get("runtime", {}) if isinstance(raw.get("runtime", {}), dict) else {}
    paths = runtime.get("paths", {}) if isinstance(runtime.get("paths", {}), dict) else {}
    services = runtime.get("services", {}) if isinstance(runtime.get("services", {}), dict) else {}
    ai = runtime.get("ai", {}) if isinstance(runtime.get("ai", {}), dict) else {}

    cfg.profile = str(profile or runtime.get("profile", cfg.profile))
    if paths.get("vault"):
        cfg.vault_path = (project_root / str(paths["vault"])).resolve() if not Path(str(paths["vault"])).is_absolute() else Path(str(paths["vault"])).resolve()
    if paths.get("runtime"):
        cfg.runtime_dir = (project_root / str(paths["runtime"])).resolve() if not Path(str(paths["runtime"])).is_absolute() else Path(str(paths["runtime"])).resolve()
    if paths.get("events"):
        cfg.events_dir = (project_root / str(paths["events"])).resolve() if not Path(str(paths["events"])).is_absolute() else Path(str(paths["events"])).resolve()
    cfg.services.update({k: bool(v) for k, v in services.items()})
    cfg.default_provider = str(ai.get("default_provider", cfg.default_provider))
    return cfg


class SecondBrainLauncher:
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.config = load_launcher_config(self.project_root, profile)
        self.config.runtime_dir.mkdir(parents=True, exist_ok=True)
        self.config.events_dir.mkdir(parents=True, exist_ok=True)
        self.config.vault_path.mkdir(parents=True, exist_ok=True)
        self.event_store = JsonlEventStore(self.config.events_dir)
        self.desktop = DesktopCommandService(self.config.vault_path)
        self.kernel = SecureAgentKernel(self.config.runtime_dir)
        self.rag = AdvancedRagIndex(self.config.vault_path)
        self.autonomous = self._build_autonomous_runtime()
        self._register_handlers()

    def _build_autonomous_runtime(self) -> AutonomousAgentRuntime:
        host = ToolHost()
        host.register("desktop.quick_capture", lambda payload: {"path": str(self.quick_capture(payload.get("text", ""), payload.get("title", "Agent Capture")))})
        host.register("desktop.notify", lambda payload: {"path": str(self.notify(payload.get("message", ""), payload.get("severity", "info")))})
        host.register("connectors.sync", lambda payload: {"results": [asdict(r) for r in self.sync_connectors()]})
        host.register("ai.ask", lambda payload: {"answer": self.ask(payload.get("prompt", ""), payload.get("task", "agent"), payload.get("provider"))})
        host.register("rag.search", lambda payload: {"hits": self.rag_search(payload.get("query", ""), int(payload.get("limit", 5)))})
        host.register("rag.answer", lambda payload: self.rag_answer(payload.get("query", ""), int(payload.get("limit", 5))))
        return AutonomousAgentRuntime(self.config.runtime_dir, host)

    def _register_handlers(self) -> None:
        self.kernel.register_handler("desktop.quick_capture", lambda payload: {"path": str(self.desktop.quick_capture(payload.get("text", ""), payload.get("title", "Quick Capture")))}, level=2, risk_score=10)
        self.kernel.register_handler("desktop.notify", lambda payload: {"path": str(self.desktop.notification(payload.get("message", ""), payload.get("severity", "info")))}, level=1, risk_score=1)
        self.kernel.register_handler("connectors.sync", lambda payload: {"results": [asdict(r) for r in self.sync_connectors()]}, level=1, risk_score=5)
        self.kernel.register_handler("ai.ask", lambda payload: {"answer": self.ask(payload.get("prompt", ""), payload.get("task", "default"))}, level=1, risk_score=5)
        self.kernel.register_handler("rag.search", lambda payload: {"hits": self.rag_search(payload.get("query", ""), int(payload.get("limit", 8)))}, level=1, risk_score=3)
        self.kernel.register_handler("rag.answer", lambda payload: self.rag_answer(payload.get("query", ""), int(payload.get("limit", 5))), level=1, risk_score=3)

    def emit(self, event_type: str, source: str, payload: dict[str, Any], risk_level: int = 1) -> Path:
        return self.event_store.append(RuntimeEvent(event_type=event_type, source=source, actor="launcher", risk_level=risk_level, payload=payload))

    def init_runtime(self) -> dict[str, str]:
        for folder in [self.config.runtime_dir, self.config.events_dir, self.config.vault_path]:
            folder.mkdir(parents=True, exist_ok=True)
        self.emit("runtime.initialized", "launcher", {"profile": self.config.profile, "platform": platform.platform()})
        return {"runtime_dir": str(self.config.runtime_dir), "events_dir": str(self.config.events_dir), "vault_path": str(self.config.vault_path)}

    def health(self) -> dict[str, Any]:
        statuses: list[ServiceStatus] = []
        statuses.append(ServiceStatus("event_store", self.config.services.get("event_store", True), "ok", str(self.config.events_dir)))
        statuses.append(ServiceStatus("desktop_commands", self.config.services.get("desktop_commands", True), "ok", str(self.config.vault_path)))
        statuses.append(ServiceStatus("agent_kernel", self.config.services.get("agent_kernel", True), "ok", str(self.config.runtime_dir / "jobs.jsonl")))
        rag_status = "ready" if self.rag.index_path.exists() else "not_indexed"
        statuses.append(ServiceStatus("advanced_rag", self.config.services.get("advanced_rag", True), rag_status, str(self.rag.index_path)))
        ar_status = self.autonomous.status()
        statuses.append(ServiceStatus("autonomous_agent", self.config.services.get("autonomous_agent", True), "ok", f"runs={ar_status['runs']}"))
        try:
            router = load_model_router(self.project_root)
            statuses.append(ServiceStatus("ai_runtime", self.config.services.get("ai_runtime", True), "ok", f"providers={','.join(sorted(router.providers))}"))
        except Exception as exc:
            statuses.append(ServiceStatus("ai_runtime", self.config.services.get("ai_runtime", True), "error", str(exc)))
        try:
            connector_cfg_path = self.project_root / "config" / "connectors_v104.json"
            raw = json.loads(connector_cfg_path.read_text(encoding="utf-8")) if connector_cfg_path.exists() else {"connectors": []}
            registry = registry_from_config(self.project_root, raw)
            statuses.append(ServiceStatus("connectors", self.config.services.get("connectors", True), "ok", f"registered={len(registry.names())}"))
        except Exception as exc:
            statuses.append(ServiceStatus("connectors", self.config.services.get("connectors", True), "error", str(exc)))
        event_summary = self.event_store.summarize()
        return {
            "profile": self.config.profile,
            "project_root": str(self.project_root),
            "python": sys.version.split()[0],
            "platform": platform.system(),
            "services": [asdict(s) for s in statuses],
            "events": event_summary,
        }

    def sync_connectors(self):
        cfg_path = self.project_root / "config" / "connectors_v104.json"
        raw = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {"connectors": []}
        registry = registry_from_config(self.project_root, raw)
        results = sync_all(registry, self.event_store)
        self.emit("connectors.sync.completed", "launcher", {"results": [asdict(r) for r in results]})
        return results

    def ask(self, prompt: str, task: str = "default", provider: str | None = None) -> str:
        router = load_model_router(self.project_root)
        answer = router.run(task, prompt, preferred_provider=provider)
        out = self.project_root / "events" / "ai_runtime_last_answer.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(answer, encoding="utf-8")
        self.emit("ai.answer.created", "launcher", {"task": task, "provider": provider or router.default_provider, "answer_path": str(out)})
        return answer

    def quick_capture(self, text: str, title: str = "Quick Capture") -> Path:
        path = self.desktop.quick_capture(text, title)
        self.emit("desktop.quick_capture.created", "launcher", {"path": str(path), "title": title})
        return path

    def notify(self, message: str, severity: str = "info") -> Path:
        path = self.desktop.notification(message, severity)
        self.emit("desktop.notification.created", "launcher", {"path": str(path), "severity": severity})
        return path

    def submit(self, action: str, payload: dict[str, Any]):
        job = self.kernel.submit(action, payload)
        self.emit("agent.job.submitted", "launcher", {"job_id": job.job_id, "action": action})
        return job

    def tick(self) -> dict[str, Any]:
        result = self.kernel.tick()
        self.emit("agent.tick.completed", "launcher", result)
        return result


    def rag_index(self) -> dict[str, Any]:
        result = self.rag.build()
        self.emit("rag.index.built", "launcher", result)
        return result

    def rag_search(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        from dataclasses import asdict as _asdict
        hits = [_asdict(h) for h in self.rag.search(query, limit=limit)]
        self.emit("rag.search.completed", "launcher", {"query": query, "hits": len(hits)})
        return hits

    def rag_answer(self, query: str, limit: int = 5) -> dict[str, Any]:
        from dataclasses import asdict as _asdict
        result = self.rag.answer(query, limit=limit)
        payload = {"query": result.query, "answer": result.answer, "citations": result.citations, "hits": [_asdict(h) for h in result.hits]}
        self.emit("rag.answer.created", "launcher", {"query": query, "citations": len(result.citations)})
        return payload

    def rag_write_answer(self, query: str, limit: int = 5) -> Path:
        path = self.rag.write_answer(query, limit=limit)
        self.emit("rag.answer.written", "launcher", {"query": query, "path": str(path)})
        return path

    def autonomous_run(self, objective: str, max_steps: int = 5) -> dict[str, Any]:
        run = self.autonomous.run_once(objective, max_steps=max_steps)
        summary = run_to_summary(run)
        self.emit("agent.autonomous.completed", "launcher", {"run_id": run.run_id, "status": run.status, "objective": objective})
        return summary

    def autonomous_status(self) -> dict[str, Any]:
        status = self.autonomous.status()
        self.emit("agent.autonomous.status", "launcher", status)
        return status

    def start_once(self) -> dict[str, Any]:
        boot = self.init_runtime()
        health = self.health()
        connector_results = [asdict(r) for r in self.sync_connectors()] if self.config.services.get("connectors", True) else []
        tick = self.tick() if self.config.services.get("agent_kernel", True) else {}
        return {"boot": boot, "health": health, "connector_results": connector_results, "tick": tick}

    def start_loop(self, interval_seconds: int = 30, max_cycles: int | None = None) -> None:
        self.init_runtime()
        cycles = 0
        while True:
            self.tick()
            cycles += 1
            if max_cycles is not None and cycles >= max_cycles:
                break
            time.sleep(interval_seconds)


def _print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain", description="SecondBrain OS unified launcher")
    parser.add_argument("--project-root", default=str(Path.cwd()), help="SecondBrain-Agent Projektordner")
    parser.add_argument("--profile", default=None, help="Startprofil, z. B. safe/dev/local-ai")
    sub = parser.add_subparsers(dest="cmd", required=False)

    sub.add_parser("init")
    sub.add_parser("health")
    sub.add_parser("sync")
    sub.add_parser("tick")
    sub.add_parser("start")
    sub.add_parser("rag-index")
    sub.add_parser("agent-status")

    p_rag_search = sub.add_parser("rag-search")
    p_rag_search.add_argument("query")
    p_rag_search.add_argument("--limit", type=int, default=8)

    p_rag_answer = sub.add_parser("rag-answer")
    p_rag_answer.add_argument("query")
    p_rag_answer.add_argument("--limit", type=int, default=5)
    p_rag_answer.add_argument("--write", action="store_true")

    p_agent_run = sub.add_parser("agent-run")
    p_agent_run.add_argument("objective")
    p_agent_run.add_argument("--max-steps", type=int, default=5)

    p_loop = sub.add_parser("loop")
    p_loop.add_argument("--interval", type=int, default=30)
    p_loop.add_argument("--max-cycles", type=int, default=None)

    p_ask = sub.add_parser("ask")
    p_ask.add_argument("prompt")
    p_ask.add_argument("--task", default="default")
    p_ask.add_argument("--provider", default=None)

    p_capture = sub.add_parser("capture")
    p_capture.add_argument("text")
    p_capture.add_argument("--title", default="Quick Capture")

    p_notify = sub.add_parser("notify")
    p_notify.add_argument("message")
    p_notify.add_argument("--severity", default="info")

    p_submit = sub.add_parser("submit")
    p_submit.add_argument("action")
    p_submit.add_argument("payload", nargs="?", default="{}", help="JSON payload")

    args = parser.parse_args(argv)
    launcher = SecondBrainLauncher(args.project_root, args.profile)
    cmd = args.cmd or "health"

    try:
        if cmd == "init":
            _print_json(launcher.init_runtime())
        elif cmd == "health":
            _print_json(launcher.health())
        elif cmd == "sync":
            _print_json([asdict(r) for r in launcher.sync_connectors()])
        elif cmd == "tick":
            _print_json(launcher.tick())
        elif cmd == "start":
            _print_json(launcher.start_once())
        elif cmd == "rag-index":
            _print_json(launcher.rag_index())
        elif cmd == "agent-status":
            _print_json(launcher.autonomous_status())
        elif cmd == "rag-search":
            _print_json(launcher.rag_search(args.query, args.limit))
        elif cmd == "rag-answer":
            if args.write:
                print(launcher.rag_write_answer(args.query, args.limit))
            else:
                _print_json(launcher.rag_answer(args.query, args.limit))
        elif cmd == "agent-run":
            _print_json(launcher.autonomous_run(args.objective, args.max_steps))
        elif cmd == "loop":
            launcher.start_loop(args.interval, args.max_cycles)
        elif cmd == "ask":
            print(launcher.ask(args.prompt, args.task, args.provider))
        elif cmd == "capture":
            print(launcher.quick_capture(args.text, args.title))
        elif cmd == "notify":
            print(launcher.notify(args.message, args.severity))
        elif cmd == "submit":
            payload = json.loads(args.payload)
            _print_json(asdict(launcher.submit(args.action, payload)))
        else:
            parser.print_help()
            return 2
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
