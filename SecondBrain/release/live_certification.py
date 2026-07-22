"""Live-Zertifizierungs-Orchestrator (Prompt 69).

Ruft die vorhandenen Live-Gates ueber einen zentralen Runner auf und wertet sie
gemeinsam aus. Schreibt keine Gates neu -- er dispatcht und aggregiert.

Statusregeln
------------
* Ein einziges ``BLOCKED`` eines Pflichtbereichs macht den Gesamtstatus
  ``BLOCKED``.
* Ein nicht konfigurierter *optionaler* Bereich ist ``SKIPPED`` und kein
  Blocker -- so verlangt es Prompt 69.
* Fehlt ein als Pflicht markierter Bereich, ist das ``BLOCKED``.
* ``PASS`` nur, wenn jeder ausgefuehrte Bereich ``PASS`` liefert und kein Bereich
  uebersprungen wurde. Sobald etwas nur ``CONDITIONAL_PASS`` ist oder ein
  optionaler Bereich fehlt, ist der Gesamtstatus ``CONDITIONAL_PASS``.

Sicherheit
----------
Der Orchestrator fuegt dem Report keine Umgebungswerte hinzu. Redaktion ist
Sache der einzelnen Gates; hier werden nur deren Statusfelder uebernommen.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

PASS, CONDITIONAL_PASS, BLOCKED, SKIPPED = "PASS", "CONDITIONAL_PASS", "BLOCKED", "SKIPPED"
SUMMARY_PATH = Path("runtime/reports/live_certification_summary.json")

# Ein Runner nimmt (project_root, env) und liefert einen Gate-Report.
Runner = Callable[[str, Mapping[str, str]], dict[str, Any]]


# --------------------------------------------------------------------------
# Standard-Runner: rufen die realen Gates lazily auf
# --------------------------------------------------------------------------


def _run_postgres(project_root: str, env: Mapping[str, str]) -> dict[str, Any]:
    from secondbrain.release.postgres_live_gate import run_postgres_live_gate
    return run_postgres_live_gate(project_root, env=dict(env), write_report=False)


def _run_provider(project_root: str, env: Mapping[str, str]) -> dict[str, Any]:
    from secondbrain.release.provider_live_gate import run_provider_live_gate
    return run_provider_live_gate(project_root, env=dict(env), write_report=False)


def _run_approval(project_root: str, env: Mapping[str, str]) -> dict[str, Any]:
    from secondbrain.release.approval_postgres_live_gate import run_approval_postgres_live_gate
    return run_approval_postgres_live_gate(project_root, write_report=False)


def _run_connector(project_root: str, env: Mapping[str, str]) -> dict[str, Any]:
    from secondbrain.release.connector_e2e_gate import run_connector_e2e_gate
    return run_connector_e2e_gate(project_root, write_report=False)


# Jeder Bereich: Runner + ob er nur laeuft, wenn konfiguriert, + welche
# Umgebungsvariable seine Konfiguration anzeigt.
DEFAULT_RUNNERS: dict[str, Runner] = {
    "postgres": _run_postgres,
    "approval": _run_approval,
    "provider": _run_provider,
    "gmail": _run_connector,
    "outlook": _run_connector,
    "google-calendar": _run_connector,
    "microsoft-calendar": _run_connector,
}

# Bereiche, die ohne Konfiguration uebersprungen statt blockiert werden.
_CONFIG_HINT: dict[str, str] = {
    "postgres": "TEST_DATABASE_URL",
    "approval": "TEST_DATABASE_URL",
    "provider": "LIVE_PROVIDERS",
    "gmail": "GMAIL_TEST_ACCOUNT",
    "outlook": "OUTLOOK_TEST_ACCOUNT",
    "google-calendar": "GOOGLE_CALENDAR_TEST_ACCOUNT",
    "microsoft-calendar": "MICROSOFT_CALENDAR_TEST_ACCOUNT",
}

# Bereiche, die zusammen "all" ergeben. Reihenfolge = Ausfuehrungsreihenfolge.
ALL_SCOPES = ("postgres", "approval", "provider", "gmail", "outlook",
              "google-calendar", "microsoft-calendar")


def resolve_scopes(scope: str) -> list[str]:
    scope = (scope or "all").strip().lower()
    if scope == "all":
        return list(ALL_SCOPES)
    if scope in DEFAULT_RUNNERS:
        return [scope]
    raise ValueError(f"unknown_scope:{scope}")


def _required_scopes(env: Mapping[str, str]) -> set[str]:
    raw = str(env.get("LIVE_CERTIFICATION_REQUIRED") or "").strip()
    return {s.strip().lower() for s in raw.split(",") if s.strip()}


def _is_configured(scope: str, env: Mapping[str, str]) -> bool:
    hint = _CONFIG_HINT.get(scope)
    return bool(hint and str(env.get(hint) or "").strip())


def run_live_certification(
    project_root: str | Path = ".",
    *,
    scope: str = "all",
    env: Mapping[str, str] | None = None,
    runners: Mapping[str, Runner] | None = None,
    write_report: bool = True,
) -> dict[str, Any]:
    values = dict(os.environ if env is None else env)
    runners = dict(runners or DEFAULT_RUNNERS)
    required = _required_scopes(values)

    report: dict[str, Any] = {
        "gate": "live_certification",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": scope,
        "required_scopes": sorted(required),
        "areas": [],
    }

    try:
        scopes = resolve_scopes(scope)
    except ValueError as exc:
        report["status"] = BLOCKED
        report["ok"] = False
        report["blockers"] = [str(exc)]
        return _finalize(report, project_root, write_report)

    for name in scopes:
        report["areas"].append(_run_area(name, project_root, values, runners, required))

    report.update(_aggregate(report["areas"]))
    return _finalize(report, project_root, write_report)


def _run_area(name: str, project_root: str | Path, env: Mapping[str, str],
              runners: Mapping[str, Runner], required: set[str]) -> dict[str, Any]:
    configured = _is_configured(name, env)
    is_required = name in required

    if not configured and not is_required:
        return {"area": name, "status": SKIPPED, "required": False,
                "reason": f"not configured ({_CONFIG_HINT.get(name)} unset)"}
    if not configured and is_required:
        return {"area": name, "status": BLOCKED, "required": True,
                "reason": f"required but not configured ({_CONFIG_HINT.get(name)} unset)"}

    runner = runners.get(name)
    if runner is None:
        return {"area": name, "status": BLOCKED, "required": is_required,
                "reason": "no runner registered"}

    try:
        result = runner(str(project_root), env)
    except Exception as exc:  # noqa: BLE001 - ein Gate-Fehler darf den Lauf nicht abbrechen
        return {"area": name, "status": BLOCKED, "required": is_required,
                "reason": f"runner raised {type(exc).__name__}"}

    status = str(result.get("status", BLOCKED))
    return {
        "area": name,
        "status": status if status in {PASS, CONDITIONAL_PASS, BLOCKED} else BLOCKED,
        "required": is_required,
        "blockers": list(result.get("blockers", [])),
        "report": result.get("report"),
    }


def _aggregate(areas: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = [a["status"] for a in areas]
    blocked = [a["area"] for a in areas if a["status"] == BLOCKED]

    if blocked:
        overall = BLOCKED
    elif any(s in {CONDITIONAL_PASS, SKIPPED} for s in statuses):
        overall = CONDITIONAL_PASS
    elif statuses and all(s == PASS for s in statuses):
        overall = PASS
    else:
        overall = CONDITIONAL_PASS

    return {
        "status": overall,
        "ok": overall != BLOCKED,
        "blocked_areas": blocked,
        "skipped_areas": [a["area"] for a in areas if a["status"] == SKIPPED],
        "summary": {s: statuses.count(s) for s in (PASS, CONDITIONAL_PASS, BLOCKED, SKIPPED) if statuses.count(s)},
    }


def _finalize(report: dict[str, Any], project_root: str | Path, write_report: bool) -> dict[str, Any]:
    report.setdefault("blockers", [])
    if write_report:
        target = Path(project_root) / SUMMARY_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report["report"] = SUMMARY_PATH.as_posix()
    return report
