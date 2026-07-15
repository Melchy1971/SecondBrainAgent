"""Frozen entry point for the Jarvis Windows build.

Responsibilities before handing control to the normal launcher:
1. Resolve the AppData home (JARVIS_HOME > %APPDATA%\\Jarvis).
2. Create the writable data layout there.
3. Migrate existing local data into the home (idempotent, never overwrites).
4. Export JARVIS_HOME and switch the working directory to the home so all
   relative data access lands in AppData, not in the (replaceable) program dir.
5. Dispatch to launcher.main with ``--project-root <home>`` and the requested
   command; the desktop shortcut passes ``native-gui``.

Special command ``smoke-test`` runs the post-install verification and exits.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _program_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    from secondbrain.install.app_home import ENV_HOME, ensure_layout, project_root, resolve_portable_home
    from secondbrain.install.migrate import migrate_local_data
    from secondbrain.install.smoke import run_smoke_test
    from secondbrain.version import get_version

    portable = (_program_dir() / ".portable").exists() or os.environ.get("JARVIS_PORTABLE") == "1"
    home = ensure_layout(resolve_portable_home(_program_dir())) if portable else project_root()
    os.environ[ENV_HOME] = str(home)

    # Migrate from an explicit previous install, else from data shipped next to
    # the executable (first-run seed). Existing user data is always preserved.
    migrate_from = os.environ.get("JARVIS_MIGRATE_FROM", "").strip() or str(_program_dir())
    try:
        migrate_local_data(migrate_from, home, version=get_version())
    except Exception:  # noqa: BLE001 - migration must never block startup
        pass

    if argv and argv[0] == "smoke-test":
        report = run_smoke_test(home)
        import json
        sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        return 0 if report["ok"] else 1

    os.chdir(home)
    command = argv or ["native-gui"]
    if "--project-root" not in command:
        command = [command[0], "--project-root", str(home), *command[1:]]

    from launcher import main as launcher_main
    return int(launcher_main(command) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
