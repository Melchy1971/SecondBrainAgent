"""Aggregationslogik des Live-Zertifizierungs-Orchestrators.

Der Orchestrator macht keine Datenbank- oder Netzwerkarbeit -- er dispatcht an
die Gates und rollt deren Status auf. Genau das wird hier gegen injizierte
Runner geprueft, ohne echte Gates.
"""

from __future__ import annotations

import json

import pytest

from secondbrain.release import live_certification as lc


def _runner(status: str):
    def run(project_root, env):  # noqa: ANN001
        return {"status": status, "blockers": [] if status != lc.BLOCKED else ["x"]}
    return run


def _all_runners(status: str) -> dict:
    return {name: _runner(status) for name in lc.ALL_SCOPES}


def _configured_env(**extra) -> dict:
    """Jeder Bereich als konfiguriert markiert, damit nichts uebersprungen wird."""
    env = {
        "TEST_DATABASE_URL": "postgresql://u:p@h:5432/db",
        "LIVE_PROVIDERS": "openai",
        "GMAIL_TEST_ACCOUNT": "g",
        "OUTLOOK_TEST_ACCOUNT": "o",
        "GOOGLE_CALENDAR_TEST_ACCOUNT": "gc",
        "MICROSOFT_CALENDAR_TEST_ACCOUNT": "mc",
    }
    env.update(extra)
    return env


def _run(scope="all", *, status="PASS", env=None, runners=None):
    return lc.run_live_certification(
        ".", scope=scope, env=env if env is not None else _configured_env(),
        runners=runners if runners is not None else _all_runners(status),
        write_report=False,
    )


# --------------------------------------------------------------------------
# Scope-Auswahl
# --------------------------------------------------------------------------


def test_all_scope_expands_to_every_area() -> None:
    assert lc.resolve_scopes("all") == list(lc.ALL_SCOPES)


def test_single_scope_runs_only_that_area() -> None:
    report = _run("postgres")
    assert [a["area"] for a in report["areas"]] == ["postgres"]


def test_unknown_scope_is_blocked() -> None:
    report = lc.run_live_certification(".", scope="does-not-exist", write_report=False)
    assert report["status"] == lc.BLOCKED
    assert any("unknown_scope" in b for b in report["blockers"])


# --------------------------------------------------------------------------
# Status-Rollup
# --------------------------------------------------------------------------


def test_all_pass_is_pass() -> None:
    assert _run(status="PASS")["status"] == lc.PASS


def test_any_blocked_is_blocked() -> None:
    runners = _all_runners("PASS")
    runners["provider"] = _runner(lc.BLOCKED)
    report = _run(runners=runners)
    assert report["status"] == lc.BLOCKED
    assert "provider" in report["blocked_areas"]


def test_conditional_pass_prevents_full_pass() -> None:
    runners = _all_runners("PASS")
    runners["postgres"] = _runner(lc.CONDITIONAL_PASS)
    assert _run(runners=runners)["status"] == lc.CONDITIONAL_PASS


def test_blocked_dominates_conditional() -> None:
    runners = _all_runners("CONDITIONAL_PASS")
    runners["approval"] = _runner(lc.BLOCKED)
    assert _run(runners=runners)["status"] == lc.BLOCKED


# --------------------------------------------------------------------------
# Optionale vs. Pflichtbereiche
# --------------------------------------------------------------------------


def test_unconfigured_optional_area_is_skipped_not_blocked() -> None:
    # Nur postgres konfiguriert; die Connector-Bereiche fehlen -> SKIPPED.
    env = {"TEST_DATABASE_URL": "postgresql://u:p@h/db", "LIVE_PROVIDERS": "openai"}
    report = _run(env=env)
    assert report["status"] != lc.BLOCKED
    assert set(report["skipped_areas"]) >= {"gmail", "outlook", "google-calendar", "microsoft-calendar"}


def test_unconfigured_required_area_is_blocked() -> None:
    env = _configured_env()
    del env["GMAIL_TEST_ACCOUNT"]
    env["LIVE_CERTIFICATION_REQUIRED"] = "gmail"
    report = _run(env=env)
    assert report["status"] == lc.BLOCKED
    assert "gmail" in report["blocked_areas"]


def test_skipped_area_forces_conditional_not_pass() -> None:
    env = {"TEST_DATABASE_URL": "postgresql://u:p@h/db"}
    report = _run(scope="all", env=env)
    # postgres+approval laufen (PASS), Rest SKIPPED -> Gesamt CONDITIONAL_PASS.
    assert report["status"] == lc.CONDITIONAL_PASS


# --------------------------------------------------------------------------
# Robustheit und Redaktion
# --------------------------------------------------------------------------


def test_runner_exception_becomes_blocked_area_not_crash() -> None:
    def boom(project_root, env):  # noqa: ANN001
        raise RuntimeError("gate exploded")

    runners = _all_runners("PASS")
    runners["postgres"] = boom
    report = _run(runners=runners)
    assert report["status"] == lc.BLOCKED
    assert any(a["area"] == "postgres" and a["status"] == lc.BLOCKED for a in report["areas"])


def test_report_does_not_leak_environment() -> None:
    env = _configured_env(TEST_DATABASE_URL="postgresql://user:s3cret@db.example.com/x")
    report = _run(env=env)
    blob = json.dumps(report)
    assert "s3cret" not in blob
    assert "db.example.com" not in blob


def test_area_can_run_separately_for_each_connector() -> None:
    for scope in ("gmail", "outlook", "google-calendar", "microsoft-calendar"):
        report = _run(scope=scope)
        assert [a["area"] for a in report["areas"]] == [scope]


# --------------------------------------------------------------------------
# Exit-Code-Kontrakt (ueber den Launcher-Rueckgabewert nachgebildet)
# --------------------------------------------------------------------------


@pytest.mark.parametrize("status,ok", [("PASS", True), ("CONDITIONAL_PASS", True), ("BLOCKED", False)])
def test_ok_flag_tracks_blocked(status: str, ok: bool) -> None:
    report = _run(status=status)
    assert report["ok"] is ok
