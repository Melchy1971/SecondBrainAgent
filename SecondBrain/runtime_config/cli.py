"""CLI für die zentrale RuntimeConfig — dieselbe Konfiguration wie die GUI.

Befehle:
    config-status                        Startvalidierung (ok|blocked) als JSON
    config-snapshot                      Maskierte Sektionssicht als JSON
    config-set KEY=WERT [...]            Werte setzen (--scope workspace|appdata)
    config-doctor                        Klartext-Diagnose; Exit-Code 1 bei blocked
Optionen:
    --project-root PFAD                  Workspace (Default: aktuelles Verzeichnis)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from secondbrain.runtime_config.service import RuntimeConfig, STATUS_BLOCKED


def _parse(raw: list[str]) -> tuple[str, list[str], dict[str, str]]:
    cmd = raw[0] if raw else "config-status"
    args: list[str] = []
    opts: dict[str, str] = {}
    rest = iter(raw[1:])
    for token in rest:
        if token in {"--project-root", "--scope"}:
            opts[token.lstrip("-").replace("-", "_")] = next(rest, "")
        else:
            args.append(token)
    return cmd, args, opts


def main(raw: list[str] | None = None) -> int:
    cmd, args, opts = _parse(list(raw or sys.argv[1:]))
    root = Path(opts.get("project_root") or Path.cwd())
    config = RuntimeConfig(root)

    if cmd == "config-status":
        print(json.dumps(config.startup_status(), indent=2, ensure_ascii=False))
        return 0

    if cmd == "config-snapshot":
        print(json.dumps(config.snapshot(), indent=2, ensure_ascii=False))
        return 0

    if cmd == "config-set":
        changes: dict[str, str] = {}
        for pair in args:
            key, sep, value = pair.partition("=")
            if not sep:
                print(json.dumps({"ok": False, "errors": [f"erwartet KEY=WERT, erhalten: {pair}"]}))
                return 2
            changes[key.strip()] = value.strip()
        result = config.set_values(changes, scope=opts.get("scope", "workspace"))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["ok"] else 1

    if cmd == "config-doctor":
        status = config.startup_status()
        print(f"Konfiguration: {status['status'].upper()}")
        for blocker in status["blockers"]:
            print(f"  BLOCKER  {blocker['key']}: {blocker['message']}")
        for warning in status["warnings"]:
            print(f"  WARNUNG  {warning['message']}")
        if not status["blockers"] and not status["warnings"]:
            print("  Keine Befunde.")
        return 1 if status["status"] == STATUS_BLOCKED else 0

    print(json.dumps({"ok": False, "errors": [f"unbekanntes Kommando: {cmd}"]}))
    return 2
