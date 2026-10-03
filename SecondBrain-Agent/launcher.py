from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Start SecondBrain Agent")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("serve", "hud"),
        default="serve",
        help="Start the API server or the workspace HUD",
    )
    parser.add_argument("--install", action="store_true", help="Run npm install explicitly")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parent
    if args.command == "hud":
        workspace_launcher = root.parent / "launcher.py"
        if not workspace_launcher.is_file():
            parser.error(f"workspace HUD launcher not found: {workspace_launcher}")
        return subprocess.run(
            [sys.executable, str(workspace_launcher), "hud"],
            cwd=workspace_launcher.parent,
            check=False,
        ).returncode

    node = shutil.which("node")
    npm = shutil.which("npm")
    if not node:
        parser.error("Node.js 20 or newer is required")
    if args.install:
        if not npm:
            parser.error("npm is required for --install")
        install = subprocess.run([npm, "install"], cwd=root, check=False)
        if install.returncode:
            return install.returncode
    return subprocess.run([node, "src/server/app.js"], cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

