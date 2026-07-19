"""Safe opt-in E2E certification for test mail and calendar accounts."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping

PASS, CONDITIONAL_PASS, BLOCKED = "PASS", "CONDITIONAL_PASS", "BLOCKED"
REPORT_PATH = Path("runtime/reports/connector_e2e_gate.json")
SUPPORTED_CONNECTORS = {"google", "microsoft"}
VALID_CONNECTOR_STATUSES = {"approval_required", "blocked", "not_configured", "passed"}


def _enabled(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes"}


def _configured(env: Mapping[str, str]) -> list[dict[str, Any]]:
    return [
        {"name": "google", "configured": _enabled(env.get("GOOGLE_E2E_TEST_ACCOUNT")) and all(env.get(k) for k in ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_E2E_TOKEN_STORE"))},
        {"name": "microsoft", "configured": _enabled(env.get("M365_E2E_TEST_ACCOUNT")) and all(env.get(k) for k in ("M365_CLIENT_ID", "M365_E2E_TOKEN_STORE"))},
    ]


def _safe_error(exc: BaseException) -> dict[str, Any]:
    return {"type": type(exc).__name__, "message": "connector live operation failed"}


def _approval_staged(runtime: Any, provider: str) -> dict[str, bool]:
    from secondbrain.connectors.scaffold.approval import ApprovalRequired
    writers = runtime.writers()
    staged = {"mail": False, "calendar": False}
    try:
        if provider == "google":
            writers["gmail"].send(["e2e-recipient@example.invalid"], "E2E approval probe", "synthetic test")
        else:
            writers["mail"].send(["e2e-recipient@example.invalid"], "E2E approval probe", "synthetic test")
    except ApprovalRequired:
        staged["mail"] = True
    try:
        writers["calendar"].create_event("E2E approval probe", "2099-01-01T10:00:00Z", "2099-01-01T10:15:00Z")
    except ApprovalRequired:
        staged["calendar"] = True
    return staged


def _evidence_complete(reads_ok: bool, incremental_ok: bool, cursor_present: bool,
                       staged: Mapping[str, bool]) -> bool:
    return reads_ok and incremental_ok and cursor_present and all(staged.values())


def _validated_probe_result(expected_name: str, result: Mapping[str, Any]) -> dict[str, Any]:
    validated = dict(result)
    if validated.get("name") != expected_name or validated.get("status") not in VALID_CONNECTOR_STATUSES:
        return {"name": expected_name, "status": "blocked", "account": "dedicated_test_account",
                "external_writes": 0, "error": {"type": "InvalidProbeResult",
                                                 "message": "connector probe returned invalid evidence"}}
    return validated


def probe_connector(config: Mapping[str, Any], env: Mapping[str, str], root: Path) -> dict[str, Any]:
    name = str(config["name"])
    sandbox = root / "runtime" / "connector-e2e" / name
    sandbox.mkdir(parents=True, exist_ok=True)
    if name == "google":
        from secondbrain.connectors.google.config import GoogleConfig
        from secondbrain.connectors.google.runtime import GoogleRuntime
        runtime = GoogleRuntime(root, config=GoogleConfig(
            client_id=str(env["GOOGLE_CLIENT_ID"]), client_secret=str(env["GOOGLE_CLIENT_SECRET"]),
            scopes=("https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/calendar"),
            token_store_path=str(Path(env["GOOGLE_E2E_TOKEN_STORE"])), cursor_store_path=str(sandbox / "cursors.json"),
            approval_store_path=str(sandbox / "approvals.json")))
        resources = ["gmail", "calendar"]
    else:
        from secondbrain.connectors.microsoft.config import GraphConfig
        from secondbrain.connectors.microsoft.runtime import M365Runtime
        runtime = M365Runtime(root, config=GraphConfig(
            client_id=str(env["M365_CLIENT_ID"]), tenant_id=str(env.get("M365_TENANT_ID") or "common"),
            scopes=("offline_access", "User.Read", "Mail.ReadWrite", "Mail.Send", "Calendars.ReadWrite"),
            token_store_path=str(Path(env["M365_E2E_TOKEN_STORE"])), cursor_store_path=str(sandbox / "cursors.json"),
            approval_store_path=str(sandbox / "approvals.json")))
        resources = ["mail", "calendar"]
    before = runtime.status()
    first = runtime.sync(resources=resources)
    second = runtime.sync(resources=resources)
    after = runtime.status()
    staged = _approval_staged(runtime, name)
    first_results, second_results = first.get("results", {}), second.get("results", {})
    reads_ok = all(first_results.get(resource, {}).get("status") == "success" for resource in resources)
    incremental_ok = all(second_results.get(resource, {}).get("status") == "success" for resource in resources)
    cursor_present = any(after.get("cursors", {}).values())
    return {"name": name, "status": "approval_required" if _evidence_complete(reads_ok, incremental_ok, cursor_present, staged) else "blocked",
        "account": "dedicated_test_account", "resources": resources, "read_sync": reads_ok, "incremental_sync": incremental_ok,
        "cursor_present": cursor_present, "token_refresh": "exercised_by_authenticator_if_expired",
        "write_approval": staged, "external_writes": 0, "cleanup": "not_required_no_external_writes",
        "cursor_changed": before.get("cursors") != after.get("cursors")}


def run_connector_e2e_gate(project_root: str | Path = ".", *, env: Mapping[str, str] | None = None,
                           probe: Callable[[Mapping[str, Any], Mapping[str, str], Path], dict[str, Any]] = probe_connector,
                           write_report: bool = True) -> dict[str, Any]:
    source = os.environ if env is None else env
    root = Path(project_root).resolve()
    required = {x.strip().lower() for x in str(source.get("REQUIRED_E2E_CONNECTORS") or "").split(",") if x.strip()}
    unknown_required = sorted(required - SUPPORTED_CONNECTORS)
    connectors: list[dict[str, Any]] = []
    for config in _configured(source):
        if not config["configured"]:
            connectors.append({"name": config["name"], "status": "blocked" if config["name"] in required else "not_configured",
                               "account": "not_configured", "external_writes": 0})
            continue
        try:
            connectors.append(_validated_probe_result(config["name"], probe(config, source, root)))
        except Exception as exc:
            connectors.append({"name": config["name"], "status": "blocked", "account": "dedicated_test_account",
                               "external_writes": 0, "error": _safe_error(exc)})
    failed = [c["name"] for c in connectors if c["status"] == "blocked"]
    failed.extend(unknown_required)
    pending = [c["name"] for c in connectors if c["status"] in {"not_configured", "approval_required"}]
    status = BLOCKED if failed else (CONDITIONAL_PASS if pending else PASS)
    report = {"schema": "secondbrain.connector_e2e_gate.v1", "generated_at": datetime.now(timezone.utc).isoformat(),
              "status": status, "ok": status != BLOCKED, "connectors": connectors, "required_connectors": sorted(required),
              "failed_connectors": failed, "pending_evidence": pending, "test_accounts_only": True,
              "writes_require_approval": True, "automatic_write_retry": False}
    if write_report:
        target = root / REPORT_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report["report"] = REPORT_PATH.as_posix()
    return report
