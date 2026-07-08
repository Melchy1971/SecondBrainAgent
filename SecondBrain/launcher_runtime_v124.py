
from __future__ import annotations
from pathlib import Path
from typing import Any
import argparse

from .launcher_runtime_v123 import SecondBrainLauncherV123
from .launcher_runtime_v113 import _print_json
from .tool_registry_v121 import ToolDefinition
from .swarm.kernel import SwarmKernel

class SecondBrainLauncherV124(SecondBrainLauncherV123):
    def __init__(self, project_root: str | Path | None = None, profile: str | None = None):
        super().__init__(project_root, profile)
        self.swarm_v124 = SwarmKernel(
            self.config.runtime_dir,
            event_bus=self.event_bus_v121,
            tool_registry=self.tool_registry_v121,
            graph_engine=self.knowledge_graph_v123,
        )
        self._register_swarm_tools()

    def _register_swarm_tools(self) -> None:
        defs = [
            ToolDefinition("swarm.status", "Read swarm status", {"type": "object", "properties": {}}, {"type": "object"}, ["swarm.read"], 1, False),
            ToolDefinition("swarm.agents", "List swarm agents", {"type": "object", "properties": {}}, {"type": "array"}, ["swarm.read"], 1, False),
            ToolDefinition("swarm.run", "Run a multi-agent swarm task", {"type": "object", "required": ["objective"], "properties": {"objective": {"type": "string"}, "priority": {"type": "string"}}}, {"type": "object"}, ["swarm.write"], 2, False),
            ToolDefinition("swarm.task", "Read swarm task", {"type": "object", "required": ["task_id"], "properties": {"task_id": {"type": "string"}}}, {"type": "object"}, ["swarm.read"], 1, False),
            ToolDefinition("swarm.consensus", "Read swarm consensus", {"type": "object", "properties": {"task_id": {"type": "string"}}}, {"type": "array"}, ["swarm.read"], 1, False),
        ]
        handlers = {
            "swarm.status": lambda p: self.swarm_status(),
            "swarm.agents": lambda p: self.swarm_agents(),
            "swarm.run": lambda p: self.swarm_run(p.get("objective", ""), p.get("priority", "normal")),
            "swarm.task": lambda p: self.swarm_task(p.get("task_id", "")),
            "swarm.consensus": lambda p: self.swarm_consensus(p.get("task_id")),
        }
        for definition in defs:
            self.tool_registry_v121.register(definition, handlers[definition.name])

    def swarm_status(self) -> dict[str, Any]:
        return self.swarm_v124.status()

    def swarm_agents(self) -> list[dict[str, Any]]:
        return self.swarm_v124.agents()

    def swarm_run(self, objective: str, priority: str = "normal") -> dict[str, Any]:
        if not objective.strip():
            raise ValueError("objective must not be empty")
        return self.swarm_v124.run(objective, priority)

    def swarm_task(self, task_id: str) -> dict[str, Any]:
        return self.swarm_v124.task(task_id)

    def swarm_history(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.swarm_v124.history_rows(limit)

    def swarm_consensus(self, task_id: str | None = None) -> list[dict[str, Any]]:
        return self.swarm_v124.consensus_rows(task_id)

    def swarm_recover(self, task_id: str) -> dict[str, Any]:
        return self.swarm_v124.recover(task_id)

    def swarm_stop(self, task_id: str) -> dict[str, Any]:
        return self.swarm_v124.stop(task_id)

    def core124_status(self) -> dict[str, Any]:
        base = self.core123_status()
        base.update({"version": "12.4", "swarm": self.swarm_status()})
        return base

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="secondbrain", description="SecondBrain OS v12.4 launcher")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--profile", default=None)
    sub = parser.add_subparsers(dest="cmd", required=False)
    for cmd in ["core-status", "swarm-status", "swarm-agents"]:
        sub.add_parser(cmd)
    p = sub.add_parser("swarm-run"); p.add_argument("objective"); p.add_argument("--priority", default="normal")
    p = sub.add_parser("swarm-task"); p.add_argument("task_id")
    p = sub.add_parser("swarm-history"); p.add_argument("--limit", type=int, default=50)
    p = sub.add_parser("swarm-consensus"); p.add_argument("task_id", nargs="?")
    p = sub.add_parser("swarm-recover"); p.add_argument("task_id")
    p = sub.add_parser("swarm-stop"); p.add_argument("task_id")
    return parser

def main(argv: list[str] | None = None) -> int:
    import sys
    raw = list(sys.argv[1:] if argv is None else argv)
    v124_cmds = {"core-status", "swarm-status", "swarm-agents", "swarm-run", "swarm-task", "swarm-history", "swarm-consensus", "swarm-recover", "swarm-stop"}
    first_cmd = next((x for x in raw if not x.startswith("-")), None)
    if first_cmd is not None and first_cmd not in v124_cmds:
        from .launcher_runtime_v123 import main as legacy_main
        return legacy_main(argv)
    parser = build_parser()
    args = parser.parse_args(argv)
    cmd = args.cmd or "core-status"
    launcher = SecondBrainLauncherV124(args.project_root, args.profile)
    try:
        if cmd == "core-status": _print_json(launcher.core124_status())
        elif cmd == "swarm-status": _print_json(launcher.swarm_status())
        elif cmd == "swarm-agents": _print_json(launcher.swarm_agents())
        elif cmd == "swarm-run": _print_json(launcher.swarm_run(args.objective, args.priority))
        elif cmd == "swarm-task": _print_json(launcher.swarm_task(args.task_id))
        elif cmd == "swarm-history": _print_json(launcher.swarm_history(args.limit))
        elif cmd == "swarm-consensus": _print_json(launcher.swarm_consensus(args.task_id))
        elif cmd == "swarm-recover": _print_json(launcher.swarm_recover(args.task_id))
        elif cmd == "swarm-stop": _print_json(launcher.swarm_stop(args.task_id))
        else: return 2
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
