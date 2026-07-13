"""Post-install smoke test.

Verifies a fresh installation can start: the home exists and is writable, the
required data directories are present, and the packaged version is readable. The
installer runs this right after copying files; a non-zero exit fails the install
visibly instead of leaving a broken shortcut.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

from secondbrain.install.app_home import DATA_SUBDIRS, resolve_home


def _check(name: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def run_smoke_test(home: str | Path | None = None, *, env: Mapping[str, str] | None = None) -> dict[str, Any]:
    home_path = Path(home) if home is not None else resolve_home(env)
    checks: list[dict[str, Any]] = []

    checks.append(_check("home_exists", home_path.exists(), str(home_path)))

    for sub in DATA_SUBDIRS:
        checks.append(_check(f"subdir:{sub}", (home_path / sub).is_dir(), str(home_path / sub)))

    writable = False
    try:
        probe = home_path / ".smoke_probe"
        probe.write_text("ok", encoding="utf-8")
        writable = probe.read_text(encoding="utf-8") == "ok"
        probe.unlink()
    except Exception as exc:  # noqa: BLE001 - reported as a failed check
        checks.append(_check("home_writable", False, str(exc)))
    else:
        checks.append(_check("home_writable", writable))

    version = ""
    try:
        from secondbrain.version import get_version
        version = get_version()
        checks.append(_check("version_readable", bool(version) and version != "0.0.0", version))
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("version_readable", False, str(exc)))

    ok = all(c["ok"] for c in checks)
    return {"schema": "jarvis.smoke.v1", "ok": ok, "status": "pass" if ok else "fail",
            "version": version, "home": str(home_path), "checks": checks}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    home = argv[0] if argv else None
    report = run_smoke_test(home)
    sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
