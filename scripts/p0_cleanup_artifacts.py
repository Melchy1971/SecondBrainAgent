from __future__ import annotations

import argparse
import shutil
from pathlib import Path

FORBIDDEN_DIR_NAMES = {"__pycache__", ".pytest_cache", ".pytest_tmp", ".mypy_cache", ".ruff_cache"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".pid", ".log"}
RUNTIME_DIRS = {"runtime", ".config"}
IGNORE_PARTS = {".git", ".venv", "venv", "env", ".env", "build", "dist", ".eggs"}


def cleanup(project_root: Path, *, dry_run: bool = False) -> list[str]:
    root = project_root.resolve()
    removed: list[str] = []
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if any(part in IGNORE_PARTS for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        should_remove = False
        if path.is_dir() and path.name in FORBIDDEN_DIR_NAMES:
            should_remove = True
        elif path.is_dir() and path.parent == root and path.name in RUNTIME_DIRS:
            should_remove = True
        elif path.is_file() and path.suffix in FORBIDDEN_SUFFIXES:
            should_remove = True
        if not should_remove:
            continue
        removed.append(rel)
        if dry_run:
            continue
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove P0-forbidden generated artifacts from the project tree.")
    parser.add_argument("--project-root", default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    removed = cleanup(args.project_root, dry_run=args.dry_run)
    for item in removed:
        print(item)
    print(f"removed={len(removed)} dry_run={args.dry_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
