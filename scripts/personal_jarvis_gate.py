#!/usr/bin/env python3
"""CLI entry point for the Personal Jarvis release gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from secondbrain.release.personal_jarvis_gate import BLOCKED, run_personal_jarvis_gate


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Personal Jarvis end-to-end release gate")
    parser.add_argument("--project-root", default=str(Path.cwd()))
    parser.add_argument("--no-write-report", action="store_true")
    args = parser.parse_args()
    report = run_personal_jarvis_gate(args.project_root, write_report=not args.no_write_report)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 2 if report["overall_status"] == BLOCKED else 0


if __name__ == "__main__":
    raise SystemExit(main())
