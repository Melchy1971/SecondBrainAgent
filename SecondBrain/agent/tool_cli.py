from __future__ import annotations

import argparse
import json
from pathlib import Path

from secondbrain.agent.tool_discovery import ToolDiscovery
from secondbrain.agent.tool_registry import ToolRegistry, ToolRegistryError


COMMANDS = {"tool-list", "tool-show", "tool-health", "tool-run", "tool-disable", "tool-enable"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain tools")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("cmd", choices=sorted(COMMANDS))
    parser.add_argument("name", nargs="?")
    parser.add_argument("payload", nargs="?", default="{}")
    parser.add_argument("--category", default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--approved", action="store_true")
    options = parser.parse_args(argv)
    root = Path(options.project_root).resolve()
    registry = ToolRegistry(root / "runtime")
    ToolDiscovery(root, registry).discover()
    try:
        if options.cmd == "tool-list":
            tools = registry.list(enabled_only=False if options.all else True, category=options.category)
            response = {"ok": True, "count": len(tools), "tools": [tool.to_dict() for tool in tools]}
        elif options.cmd == "tool-health":
            response = {"ok": True, **registry.health(options.name)}
        else:
            if not options.name:
                raise ValueError("tool_name_required")
            if options.cmd == "tool-show":
                response = {"ok": True, "tool": registry.get(options.name).to_dict()}
            elif options.cmd == "tool-disable":
                response = {"ok": True, "tool": registry.set_enabled(options.name, False).to_dict()}
            elif options.cmd == "tool-enable":
                response = {"ok": True, "tool": registry.set_enabled(options.name, True).to_dict()}
            else:
                payload = json.loads(options.payload)
                if not isinstance(payload, dict):
                    raise ValueError("tool_payload_must_be_object")
                result = registry.run(options.name, payload, approved=options.approved)
                response = result.to_dict()
        print(json.dumps(response, indent=2, ensure_ascii=False, default=str))
        return 0 if response.get("ok", False) else 1
    except (ToolRegistryError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2, ensure_ascii=False))
        return 2
