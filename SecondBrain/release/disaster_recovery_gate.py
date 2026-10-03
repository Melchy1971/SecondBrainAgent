"""Disaster-Recovery- und Vault-Gate (Prompt 71).

Umfang dieser Stufe
-------------------
Hier prüfbar, gegen echte Kryptografie:
* verschlüsselter Backup-Roundtrip (encrypt/decrypt)
* falscher Schlüssel wird abgewiesen
* manipuliertes Backup-Blob wird abgewiesen
* Secret-Leak-Scan: kein Klartext-Secret im Backup-Artefakt
* Schlüsselrotation: neuer Schlüssel liest alte Daten nach Re-Wrap
* Rollback stellt den Vorzustand wieder her

Delegiert / nur mit Live-Umgebung nachweisbar (als ``delegated`` markiert):
* pgvector nach Restore -> PostgreSQL-Live-Gate
* Approvals und Audit nach Restore -> Approval-Live-Gate

Die Orchestrierung ist über injizierbare Schritte testbar, ohne echtes
Dateisystem-Backup. Der Kryptografieteil läuft real.

Sicherheit
----------
Der Report enthält keine Schlüssel, keine Klartext-Secrets und keine Pfade zu
Vault-Dateien. ``_safe_error`` gibt nur den Fehlertyp aus.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

PASS, CONDITIONAL_PASS, BLOCKED = "PASS", "CONDITIONAL_PASS", "BLOCKED"
REPORT_PATH = Path("runtime/reports/disaster_recovery_gate.json")

# Diese Nachweise werden bei realen Schritten nicht mehr delegiert.
DELEGATED_CHECKS: tuple[str, ...] = ()

# Markerwoerter, die niemals im Klartext in einem Backup-Artefakt stehen duerfen.
_SECRET_MARKERS = ("BEGIN PRIVATE KEY", "password=", "api_key", "secret_key", "aws_secret")


def _check(name: str, ok: bool, *, detail: str = "", blocking: bool = True) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail, "blocking": bool(blocking)}


def _safe_error(exc: BaseException) -> dict[str, str]:
    return {"type": type(exc).__name__, "message": "recovery operation failed"}


# --------------------------------------------------------------------------
# Kryptografie-Selbsttest -- laeuft real
# --------------------------------------------------------------------------


def _crypto_checks() -> list[dict[str, Any]]:
    from secondbrain.secret_manager.crypto import (
        constant_time_equal,
        decrypt,
        encrypt,
        random_key,
    )

    checks: list[dict[str, Any]] = []
    payload = b"workspace=ws-a;token=do-not-log;rows=42"
    aad = b"backup-manifest-v1"

    key = random_key()
    blob = encrypt(key, payload, aad=aad)

    # Roundtrip
    try:
        restored = decrypt(key, blob, aad=aad)
        checks.append(_check("encrypted_backup_roundtrip", restored == payload))
    except Exception as exc:  # noqa: BLE001
        checks.append(_check("encrypted_backup_roundtrip", False, detail=type(exc).__name__))

    # Falscher Schluessel
    rejected = False
    try:
        decrypt(random_key(), blob, aad=aad)
    except Exception:
        rejected = True
    checks.append(_check("wrong_key_is_rejected", rejected))

    # Manipuliertes Ciphertext
    tampered = dict(blob)
    ct = bytearray(_b64d(tampered.get("ct") or tampered.get("ciphertext") or ""))
    if ct:
        ct[0] ^= 0x01
        for field in ("ct", "ciphertext"):
            if field in tampered:
                tampered[field] = _b64e(bytes(ct))
    tamper_rejected = False
    try:
        decrypt(key, tampered, aad=aad)
    except Exception:
        tamper_rejected = True
    checks.append(_check("tampered_backup_is_rejected", tamper_rejected))

    # Verschluesseltes Artefakt enthaelt kein Klartext-Secret
    serialized = json.dumps(blob)
    leak = any(marker.lower() in serialized.lower() for marker in ("do-not-log", "ws-a", "token="))
    checks.append(_check("vault_artifact_has_no_plaintext", not leak))

    # AAD-Bindung: falscher Kontext scheitert
    aad_rejected = False
    try:
        decrypt(key, blob, aad=b"other-context")
    except Exception:
        aad_rejected = True
    checks.append(_check("aad_context_binding", aad_rejected))

    checks.append(_check("constant_time_compare_available",
                         constant_time_equal(b"a", b"a") and not constant_time_equal(b"a", b"b"),
                         blocking=False))
    return checks


def _key_rotation_check() -> dict[str, Any]:
    """Alte Daten bleiben nach Re-Wrap unter neuem Schluessel lesbar."""
    from secondbrain.secret_manager.crypto import decrypt, encrypt, random_key

    try:
        payload = b"rotate-me"
        old = random_key()
        blob = encrypt(old, payload)
        plain = decrypt(old, blob)
        new = random_key()
        rewrapped = encrypt(new, plain)
        ok = decrypt(new, rewrapped) == payload and new != old
        return _check("key_rotation_preserves_data", ok)
    except Exception as exc:  # noqa: BLE001
        return _check("key_rotation_preserves_data", False, detail=type(exc).__name__)


def _b64e(raw: bytes) -> str:
    import base64
    return base64.b64encode(raw).decode("ascii")


def _b64d(text: str) -> bytes:
    import base64
    try:
        return base64.b64decode(text)
    except Exception:  # noqa: BLE001
        return b""


# --------------------------------------------------------------------------
# Backup-/Restore-Orchestrierung -- Schritte injizierbar
# --------------------------------------------------------------------------


class RecoverySteps:
    """Standardschritte. Für Tests durch Fakes ersetzbar.

    Jeder Schritt liefert ein dict mit mindestens ``ok`` und optional
    ``checksum``. Die Schritte kapseln die tatsächliche Dateisystem-/DB-Arbeit,
    damit die Orchestrierung ohne echtes Backup prüfbar bleibt.
    """

    def snapshot_state(self, project_root: Path) -> dict[str, Any]:
        return {"ok": True, "checksum": "state-before"}

    def create_backup(self, project_root: Path) -> dict[str, Any]:
        return {"ok": True, "checksum": "backup-1", "artifact": "backup-1.enc"}

    def validate_checksum(self, backup: dict[str, Any]) -> dict[str, Any]:
        return {"ok": bool(backup.get("checksum"))}

    def mutate_state(self, project_root: Path) -> dict[str, Any]:
        return {"ok": True, "checksum": "state-mutated"}

    def restore(self, backup: dict[str, Any], project_root: Path) -> dict[str, Any]:
        return {"ok": True, "checksum": backup.get("checksum")}

    def rollback(self, snapshot: dict[str, Any], project_root: Path) -> dict[str, Any]:
        return {"ok": True, "checksum": snapshot.get("checksum")}


def _recovery_checks(steps: RecoverySteps, project_root: Path) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []

    snapshot = steps.snapshot_state(project_root)
    checks.append(_check("snapshot_before_restore", snapshot.get("ok", False)))

    backup = steps.create_backup(project_root)
    checks.append(_check("full_backup", backup.get("ok", False)))

    checksum = steps.validate_checksum(backup)
    checks.append(_check("backup_checksum_valid", checksum.get("ok", False)))

    steps.mutate_state(project_root)  # simulierte Veraenderung zwischen Backup und Restore

    restored = steps.restore(backup, project_root)
    # Ein Restore, der den Backup-Zustand nicht exakt wiederherstellt, ist
    # Datenverlust -- der haerteste Blocker.
    restore_ok = restored.get("ok", False) and restored.get("checksum") == backup.get("checksum")
    checks.append(_check("full_restore_matches_backup", restore_ok))

    # Rollback stellt den Vorzustand wieder her, nicht den Backup-Zustand.
    rolled = steps.rollback(snapshot, project_root)
    rollback_ok = rolled.get("ok", False) and rolled.get("checksum") == snapshot.get("checksum")
    checks.append(_check("rollback_restores_prior_state", rollback_ok))

    failure_checks = getattr(steps, "failure_checks", None)
    if callable(failure_checks):
        for entry in failure_checks(project_root):
            checks.append(_check(entry["name"], entry.get("ok", False),
                                 detail=entry.get("detail", ""),
                                 blocking=entry.get("blocking", True)))

    # Optionale DB-Checks (echtes pg_dump/pg_restore) -- nur reale Schritte
    # liefern sie; hermetische Fake-Schritte haben die Methode nicht.
    db_checks = getattr(steps, "database_checks", None)
    if callable(db_checks):
        for entry in db_checks(project_root):
            checks.append(_check(entry["name"], entry.get("ok", False),
                                 detail=entry.get("detail", ""),
                                 blocking=entry.get("blocking", True)))

    return checks


# --------------------------------------------------------------------------
# Gate
# --------------------------------------------------------------------------


def run_disaster_recovery_gate(
    project_root: str | Path = ".",
    *,
    steps: RecoverySteps | None = None,
    env: dict[str, str] | None = None,
    write_report: bool = True,
) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    root = Path(project_root)
    # Default: echte Schritte (verschluesseltes FS-Backup + optional pg-Roundtrip).
    # Injektion bleibt fuer hermetische Kontrollflusstests erhalten.
    injected = steps is not None
    if steps is None:
        from secondbrain.release.backup_engine import RealRecoverySteps
        steps = RealRecoverySteps(root, env=values)

    report: dict[str, Any] = {
        "gate": "disaster_recovery_gate",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "delegated_checks": list(DELEGATED_CHECKS),
        "steps": "injected" if injected else "real",
        "checks": [],
    }

    try:
        report["checks"].extend(_crypto_checks())
        report["checks"].append(_key_rotation_check())
        report["checks"].extend(_recovery_checks(steps, root))
    except Exception as exc:  # noqa: BLE001
        report["checks"].append(_check("disaster_recovery", False, detail=type(exc).__name__))
        report["error"] = _safe_error(exc)
    finally:
        cleanup = getattr(steps, "cleanup", None)
        if callable(cleanup):
            cleanup()

    blocking = [c["name"] for c in report["checks"] if c["blocking"] and not c["ok"]]
    warnings = [c["name"] for c in report["checks"] if not c["blocking"] and not c["ok"]]
    report["blockers"] = blocking
    report["warnings"] = warnings

    real_db_executed = not injected and any(
        check["name"] == "pg_restore_into_empty_database" and check["ok"]
        for check in report["checks"]
    )
    if blocking:
        report["status"] = BLOCKED
    elif real_db_executed:
        report["status"] = PASS
    else:
        # Injizierte Schritte oder fehlende Test-DB sind kein realer Nachweis.
        report["status"] = CONDITIONAL_PASS
    report["ok"] = report["status"] != BLOCKED

    if write_report:
        target = root / REPORT_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report["report"] = REPORT_PATH.as_posix()
    return report
