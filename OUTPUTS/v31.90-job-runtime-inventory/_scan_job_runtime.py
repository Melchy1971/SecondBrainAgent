"""Einmaliger Analyse-Scan fuer das Job-Runtime-Inventar (Prompt 70 Phase 1).

Kein Produktionscode. Laeuft read-only ueber den Baum und meldet Kandidaten,
die eigene Nebenlaeufigkeit oder eigenes Prozess-Handling mitbringen.
"""

from __future__ import annotations

import ast
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
SOURCES = ["SecondBrain", "scripts", "launcher.py", "secondbrain.py"]

SKIP_PARTS = {"tests", "test", "__pycache__", "_archive_starters", "OUTPUTS", "backups", "archive"}

MARKERS = {
    "thread": ("Thread",),
    "pool": ("ThreadPoolExecutor", "ProcessPoolExecutor"),
    "queue": ("Queue", "SimpleQueue", "LifoQueue", "PriorityQueue"),
    "subprocess": ("Popen", "run", "call", "check_output", "check_call"),
    "async": ("create_task", "gather", "run_in_executor"),
}


def _iter_files() -> list[Path]:
    files: list[Path] = []
    for entry in SOURCES:
        target = ROOT / entry
        if target.is_file() and target.suffix == ".py":
            files.append(target)
        elif target.is_dir():
            for path in target.rglob("*.py"):
                if SKIP_PARTS & set(path.parts):
                    continue
                files.append(path)
    return files


def _attr_chain(node: ast.AST) -> str:
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def analyse(path: Path) -> dict:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return {}

    hits: dict[str, list[int]] = defaultdict(list)
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            name = _attr_chain(node.func) or getattr(node.func, "id", "")
            leaf = name.split(".")[-1]
            for kind, needles in MARKERS.items():
                if leaf in needles:
                    if kind == "subprocess" and "subprocess" not in name and "subprocess" not in imports:
                        continue
                    if kind == "queue" and "Queue" not in leaf:
                        continue
                    hits[kind].append(node.lineno)
        elif isinstance(node, ast.While):
            hits["while_loop"].append(node.lineno)

    # Retry-Schleifen und Wartezeiten heuristisch
    for i, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if "time.sleep" in stripped:
            hits["sleep"].append(i)
        if stripped.startswith("for ") and "range(" in stripped and (
            "attempt" in stripped or "retry" in stripped or "tries" in stripped
        ):
            hits["retry_loop"].append(i)

    if not hits:
        return {}

    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "loc": len(source.splitlines()),
        "imports_job_runtime": any(
            marker in source for marker in ("SecondBrain.jobs", "from .jobs", "jobs.service", "JobService")
        ),
        "hits": {kind: sorted(set(lines)) for kind, lines in sorted(hits.items())},
    }


def main() -> None:
    results = [r for r in (analyse(p) for p in _iter_files()) if r]

    # Nur echte Nebenlaeufigkeits-/Prozess-Kandidaten behalten.
    strong = {"thread", "pool", "queue", "subprocess", "retry_loop"}
    candidates = [r for r in results if strong & set(r["hits"])]
    candidates.sort(key=lambda r: (-len(strong & set(r["hits"])), r["path"]))

    summary: dict[str, int] = defaultdict(int)
    for r in candidates:
        for kind in r["hits"]:
            summary[kind] += 1

    print(json.dumps({
        "scanned_files": len(_iter_files()),
        "candidates": len(candidates),
        "marker_summary": dict(sorted(summary.items())),
        "results": candidates,
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
