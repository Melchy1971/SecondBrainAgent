"""v30.47 - CLI des Document Preview Centers (JSON-Ausgabe, launcher-kompatibel)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .service import DocumentPreviewService


def _out(payload: Any) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="secondbrain document-preview")
    parser.add_argument("cmd", choices=[
        "document-preview", "document-preview-gui", "document-preview-status",
        "document-preview-open", "document-preview-metadata", "document-preview-search",
        "document-preview-ocr", "document-preview-annotate", "document-preview-annotations",
        "document-preview-version-snapshot", "document-preview-versions",
    ])
    parser.add_argument("args", nargs="*")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--max-chars", type=int, default=20000)
    ns, _ = parser.parse_known_args(argv)
    service = DocumentPreviewService(ns.project_root)

    if ns.cmd in {"document-preview", "document-preview-gui"}:
        from .gui import run_gui
        return run_gui(ns.project_root)

    def _ref(position: int = 0) -> str:
        return ns.args[position] if len(ns.args) > position else ""

    if ns.cmd == "document-preview-status":
        payload = service.status()
    elif ns.cmd == "document-preview-open":
        payload = service.preview(_ref(), max_chars=ns.max_chars)
    elif ns.cmd == "document-preview-metadata":
        payload = service.metadata(_ref())
    elif ns.cmd == "document-preview-search":
        payload = service.search(_ref(), _ref(1))
    elif ns.cmd == "document-preview-ocr":
        payload = service.ocr_overlay(_ref(), page=ns.page)
    elif ns.cmd == "document-preview-annotate":
        payload = service.annotate(_ref(), " ".join(ns.args[1:]), page=ns.page)
    elif ns.cmd == "document-preview-annotations":
        payload = service.annotations(_ref())
    elif ns.cmd == "document-preview-version-snapshot":
        payload = service.snapshot_version(_ref())
    elif ns.cmd == "document-preview-versions":
        payload = service.versions(_ref())
    else:  # pragma: no cover
        payload = {"ok": False, "error": "unknown_command", "cmd": ns.cmd}
    _out(payload)
    return 0 if payload.get("ok") else 1
