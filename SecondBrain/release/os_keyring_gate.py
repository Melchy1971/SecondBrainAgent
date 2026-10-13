"""OS-Keyring-Gate: sicheres Schluesselbackend und echter Speicher-Rundlauf.

Geprueft wird zweierlei:

1. Die Konfiguration loest auf das sichere OS-Keyring-Backend auf
   (``resolve_key_provider``), nicht auf das unsichere Env-Backend.
2. Ein Zufallswert laesst sich unter einem eindeutigen Gate-Dienstnamen im
   Keyring speichern, lesen und wieder entfernen. Der Wert erscheint nie im
   Bericht; der Eintrag wird auch im Fehlerfall geloescht.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping
from uuid import uuid4

from secondbrain.release.evidence import seal
from secondbrain.secret_manager.key_provider import (
    KeyNotFound,
    KeyProviderError,
    OSKeyringKeyProvider,
    resolve_key_provider,
)

PASS, BLOCKED = "PASS", "BLOCKED"
SCHEMA = "secondbrain.os_keyring_gate.v1"
REPORT_PATH = Path("runtime/reports/os_keyring_gate.json")
_ALIAS = "gate-roundtrip"


def _roundtrip(provider: OSKeyringKeyProvider) -> dict[str, bool]:
    """Ueber die oeffentliche Schnittstelle: create, load, revoke."""
    result = {"stored": False, "read_back": False, "removed": False}
    try:
        key = provider.create(_ALIAS)
        result["stored"] = True
        result["read_back"] = provider.load(_ALIAS) == key
    finally:
        provider.revoke(_ALIAS)
        try:
            provider.load(_ALIAS)
        except KeyNotFound:
            result["removed"] = True
        except KeyProviderError:
            result["removed"] = False
    return result


def run_os_keyring_gate(
    project_root: str | Path = ".",
    *,
    env: Mapping[str, str] | None = None,
    keyring_factory: Callable[[str], OSKeyringKeyProvider] | None = None,
    write_report: bool = True,
) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    root = Path(project_root).resolve()
    checks: list[dict[str, Any]] = []
    backend, secure = "unavailable", False
    try:
        provider = resolve_key_provider(values)
        backend, secure = str(provider.name), bool(provider.secure)
        checks.append({"name": "configured_backend_is_os_keyring", "ok": backend == "os_keyring" and secure,
                       "detail": f"backend={backend}, secure={secure}"})
    except KeyProviderError as exc:
        checks.append({"name": "configured_backend_is_os_keyring", "ok": False, "detail": type(exc).__name__})

    # Eindeutiger Dienstname: kollidiert nie mit dem produktiven Master-Key.
    factory = keyring_factory or (lambda service: OSKeyringKeyProvider(service=service))
    gate_keyring = factory(f"secondbrain-gate-{uuid4().hex[:12]}")
    if gate_keyring.available():
        try:
            outcome = _roundtrip(gate_keyring)
            checks.append({"name": "keyring_roundtrip", "ok": outcome["stored"] and outcome["read_back"],
                           "detail": f"stored={outcome['stored']}, read_back={outcome['read_back']}"})
            checks.append({"name": "keyring_cleanup", "ok": outcome["removed"]})
        except KeyProviderError as exc:
            checks.append({"name": "keyring_roundtrip", "ok": False, "detail": type(exc).__name__})
    else:
        checks.append({"name": "keyring_roundtrip", "ok": False, "detail": "secure OS keyring unavailable"})

    status = PASS if checks and all(c["ok"] for c in checks) else BLOCKED
    report = seal({
        "status": status, "ok": status == PASS, "backend": backend, "secure_backend": secure,
        "checks": checks, "keyring_backend": gate_keyring.health().get("keyring_backend"),
    }, schema=SCHEMA, root=root, env=values)
    if write_report:
        target = root / REPORT_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report = {**report, "report": REPORT_PATH.as_posix()}
    return report
