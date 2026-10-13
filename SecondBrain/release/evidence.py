"""Commit-gebundener Umschlag fuer Gate-Nachweise.

Jedes Gate, dessen Bericht vom ``jarvis-1.0-gate`` aggregiert wird, versiegelt
ihn hier beim Schreiben. Produzent und Aggregator nutzen denselben Hash
(:func:`canonical_hash`), damit die Integritaetspruefung nicht auseinanderlaeuft.

Umschlagfelder
--------------
``schema``          Berichtsschema des Gates.
``commit_sha``      ``git rev-parse HEAD`` zum Zeitpunkt des Laufs.
``worktree_clean``  Keine uncommitteten Aenderungen an versionierten Dateien --
                    sonst behauptet der Nachweis einen Commit, prueft aber
                    anderen Code.
``environment``     Wo der Nachweis entstand. Nie geraten: ``production`` und
                    ``clean-windows`` nur bei expliziter Angabe
                    (``SECONDBRAIN_EVIDENCE_ENVIRONMENT``); in GitHub Actions
                    ``ci``; sonst ``local``.
``generated_at`` / ``expires_at``  UTC, Gueltigkeit standardmaessig 24 h.
``evidence_sha256`` SHA-256 ueber alle uebrigen Felder.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

ENV_VARIABLE = "SECONDBRAIN_EVIDENCE_ENVIRONMENT"
ENVIRONMENTS = frozenset({"production", "clean-windows", "ci", "local", "test"})
DEFAULT_TTL_HOURS = 24


def canonical_hash(report: Mapping[str, Any]) -> str:
    payload = {key: value for key, value in report.items() if key != "evidence_sha256"}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout


def git_commit(root: str | Path) -> str | None:
    out = _git(Path(root), "rev-parse", "HEAD")
    return out.strip() if out else None


def worktree_clean(root: str | Path) -> bool:
    """Keine Aenderungen an versionierten Dateien (Untracked bleibt ausser Betracht:
    Berichte unter runtime/ sind ignoriert, neue Quelldateien sind nicht Teil von HEAD)."""
    out = _git(Path(root), "status", "--porcelain", "--untracked-files=no")
    return out is not None and out.strip() == ""


def evidence_environment(env: Mapping[str, str] | None = None) -> str:
    values = os.environ if env is None else env
    explicit = str(values.get(ENV_VARIABLE, "")).strip().lower()
    if explicit:
        if explicit not in ENVIRONMENTS:
            raise ValueError(f"{ENV_VARIABLE} must be one of {sorted(ENVIRONMENTS)}")
        return explicit
    if str(values.get("GITHUB_ACTIONS", "")).lower() == "true":
        return "ci"
    return "local"


def _parse(value: Any) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else None


def seal(
    report: Mapping[str, Any],
    *,
    schema: str,
    root: str | Path,
    environment: str | None = None,
    env: Mapping[str, str] | None = None,
    ttl_hours: int = DEFAULT_TTL_HOURS,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Liefert eine versiegelte Kopie von ``report``.

    Ein vorhandenes, zeitzonenbehaftetes ``generated_at`` bleibt erhalten; sonst
    gilt ``now``. ``environment`` ueberschreibt die Ableitung nur fuer Nachweise,
    deren Herkunft feststeht (z. B. CI-Ergebnisse, die per API gelesen werden).
    """
    if environment is not None and environment not in ENVIRONMENTS:
        raise ValueError(f"unknown evidence environment: {environment}")
    sealed = {key: value for key, value in report.items() if key != "evidence_sha256"}
    if sealed.get("schema") not in (None, schema):
        raise ValueError(f"schema mismatch: {sealed.get('schema')} != {schema}")
    generated = _parse(sealed.get("generated_at")) or (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    sealed.update(
        schema=schema,
        commit_sha=git_commit(root),
        worktree_clean=worktree_clean(root),
        environment=environment or evidence_environment(env),
        generated_at=generated.isoformat(),
        expires_at=(generated + timedelta(hours=ttl_hours)).isoformat(),
    )
    sealed["evidence_sha256"] = canonical_hash(sealed)
    return sealed
