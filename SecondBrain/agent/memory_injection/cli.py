"""v30.64 Agent Memory Injection - launcher CLI.

Commands wired into launcher.py:
    agent-memory-preview  --query TEXT [--memories PATH] [--workspace ID]
                          [--limit N] [--budget TOKENS] [--privacy] [--require-source]
    agent-memory-inject   (same as preview) [--actor NAME] [--agent-id ID]
    agent-memory-audit    [--agent-id ID] [--limit N]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .service import MemoryInjectionService


def _out(obj) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-memory")
    parser.add_argument("cmd")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--profile", default=None)
    parser.add_argument("--memories", default=None, help="JSON file with memory records")
    parser.add_argument("--query", default="")
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--budget", type=int, default=None)
    parser.add_argument("--min-relevance", type=float, default=0.0)
    parser.add_argument("--privacy", action="store_true")
    parser.add_argument("--require-source", action="store_true")
    parser.add_argument("--actor", default="agent")
    parser.add_argument("--agent-id", default="")
    parser.add_argument("--audit-limit", type=int, default=100)
    return parser


def _args_dict(args) -> dict:
    return {
        "text": args.query,
        "workspace_id": args.workspace,
        "limit": args.limit,
        "token_budget": args.budget,
        "min_relevance": args.min_relevance,
        "privacy_mode": args.privacy,
        "require_source": args.require_source,
    }


def main(argv: list[str] | None = None, *, root: str | Path | None = None) -> int:
    args, _ = build_parser().parse_known_args(argv)
    service = MemoryInjectionService(root or args.project_root)
    cmd = args.cmd

    if cmd in {"agent-memory-preview", "agent-memory-inject"}:
        if args.memories:
            try:
                service.load_memories(args.memories)
            except Exception as exc:
                _out({"ok": False, "error": f"memories_load_failed:{exc}"})
                return 2
        payload = (service.preview(_args_dict(args)) if cmd == "agent-memory-preview"
                   else service.inject(_args_dict(args), actor=args.actor, agent_id=args.agent_id))
        _out(payload)
        return 0

    if cmd == "agent-memory-audit":
        _out(service.audit(args.agent_id or None, limit=args.audit_limit))
        return 0

    _out({"ok": False, "error": f"unknown_command:{cmd}"})
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
