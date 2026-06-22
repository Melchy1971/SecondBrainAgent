from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os
import sqlite3
import sys

from .config import load_simple_yaml
from .event_bus_v121 import EventBus
from .module_registry import ModuleRegistry


@dataclass(frozen=True)
class RuntimeConfigSnapshot:
    project_root: str
    profile: str
    runtime_dir: str
    config_files: dict[str, bool]
    settings_keys: list[str]
    production_keys: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeReadinessSnapshot:
    project_root: str
    runtime_dir: str
    config_ok: bool
    secrets_ok: bool
    database_ok: bool
    event_bus_ok: bool
    state_ok: bool
    checks: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


SENSITIVE_KEY_MARKERS = ("token", "secret", "password", "api_key", "apikey", "private_key")
PLACEHOLDER_MARKERS = ("", "change_me", "changeme", "todo", "example", "placeholder", "your_", "xxx")

REQUIRED_CONFIG_FILES = (
    "settings.yaml",
    "runtime.yaml",
    "production.yaml",
    "security.yaml",
    "connectors.yaml",
)

CRITICAL_COMMANDS = (
    "status",
    "health",
    "modules",
    "module-status",
    "command-index",
    "p0-doctor",
    "p0-gate",
    "p0-report",
    "p0-smoke",
    "p0-contract",
    "p0-readiness",
    "p0-bootstrap",
    "p0-production",
    "p0-audit",
    "desktop-status",
    "mobile16-status",
)


def load_runtime_snapshot(project_root: str | Path, profile: str | None = None) -> RuntimeConfigSnapshot:
    root = Path(project_root).resolve()
    config_dir = root / "config"
    settings = load_simple_yaml(config_dir / "settings.yaml")
    runtime_cfg = load_simple_yaml(config_dir / "runtime.yaml")
    production = load_simple_yaml(config_dir / "production.yaml")
    runtime_dir = runtime_cfg.get("runtime_dir") or settings.get("runtime_dir") or str(root / "runtime")
    runtime_path = Path(str(runtime_dir))
    if not runtime_path.is_absolute():
        runtime_path = root / runtime_path
    return RuntimeConfigSnapshot(
        project_root=str(root),
        profile=profile or "default",
        runtime_dir=str(runtime_path.resolve()),
        config_files={name: (config_dir / name).exists() for name in REQUIRED_CONFIG_FILES},
        settings_keys=sorted(settings.keys()),
        production_keys=sorted(production.keys()),
    )


def _check(name: str, ok: bool, severity: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "severity": severity, "detail": detail or {}}


def _runtime_writable(path: Path) -> tuple[bool, str | None]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".p0_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True, None
    except Exception as exc:  # pragma: no cover - platform boundary
        return False, str(exc)


def _stable_checks(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    severity_rank = {"blocker": 0, "warning": 1, "info": 2}
    return sorted(checks, key=lambda item: (item["ok"], severity_rank.get(item["severity"], 9), item["name"]))


def write_p0_report(payload: dict[str, Any], project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    reports_dir = root / "runtime" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "p0_gate_latest.json"
    report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return {"path": str(report_path), "bytes": report_path.stat().st_size}



def _write_named_report(payload: dict[str, Any], project_root: str | Path, filename: str) -> dict[str, Any]:
    root = Path(project_root).resolve()
    reports_dir = root / "runtime" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / filename
    report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return {"path": str(report_path), "bytes": report_path.stat().st_size}



def _flatten_config(data: dict[str, Any], prefix: str = "") -> list[tuple[str, Any]]:
    rows: list[tuple[str, Any]] = []
    for key, value in data.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            rows.extend(_flatten_config(value, path))
        else:
            rows.append((path, value))
    return rows


def _looks_sensitive(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(marker in normalized for marker in SENSITIVE_KEY_MARKERS)


def _is_placeholder(value: Any) -> bool:
    text = str(value).strip().lower()
    return any(text == marker or text.startswith(marker) for marker in PLACEHOLDER_MARKERS)


def secrets_readiness(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    config_dir = root / "config"
    template_path = config_dir / "secrets.template.yaml"
    live_path = config_dir / "secrets.yaml"
    security = load_simple_yaml(config_dir / "security.yaml")
    live = load_simple_yaml(live_path)
    flat_live = _flatten_config(live)
    leaked_placeholders = [key for key, value in flat_live if _looks_sensitive(key) and _is_placeholder(value)]
    live_secret_keys = [key for key, _ in flat_live if _looks_sensitive(key)]
    encryption_mode = str(security.get("secrets", {}).get("encryption") or security.get("secret_encryption") or "none")
    checks = [
        _check("secrets_template_exists", template_path.exists(), "warning", {"path": str(template_path)}),
        _check("live_secrets_file_absent_or_non_placeholder", not leaked_placeholders, "blocker", {"placeholder_keys": leaked_placeholders, "live_file_exists": live_path.exists()}),
        _check("secret_encryption_declared", encryption_mode not in {"", "none", "false", "base64"}, "warning", {"mode": encryption_mode}),
    ]
    blockers = sum(1 for c in checks if not c["ok"] and c["severity"] == "blocker")
    warnings = sum(1 for c in checks if not c["ok"] and c["severity"] == "warning")
    return {
        "ok": blockers == 0,
        "status": "pass" if blockers == 0 else "blocked",
        "warnings": warnings,
        "blockers": blockers,
        "live_file_exists": live_path.exists(),
        "live_secret_key_count": len(live_secret_keys),
        "checks": _stable_checks(checks),
    }


def database_readiness(project_root: str | Path, profile: str | None = None) -> dict[str, Any]:
    root = Path(project_root).resolve()
    config_dir = root / "config"
    production = load_simple_yaml(config_dir / "production.yaml")
    runtime_cfg = load_simple_yaml(config_dir / "runtime.yaml")
    database_cfg = production.get("database", {}) if isinstance(production.get("database"), dict) else {}
    database_url = os.environ.get("DATABASE_URL") or database_cfg.get("url") or runtime_cfg.get("database_url")
    db_mode = "external" if database_url else "local_sqlite_probe"
    checks: list[dict[str, Any]] = []
    if database_url:
        url = str(database_url)
        engine = "postgresql" if url.startswith(("postgresql://", "postgres://")) else "unknown"
        checks.append(_check("database_url_declared", True, "blocker", {"engine": engine}))
        checks.append(_check("postgresql_url_for_production", engine == "postgresql", "warning", {"engine": engine}))
        checks.append(_check("pgvector_assumption_declared", bool(database_cfg.get("pgvector") or production.get("pgvector")), "warning", {"pgvector": database_cfg.get("pgvector") or production.get("pgvector")}))
    else:
        db_path = root / "runtime" / "p0_readiness.sqlite3"
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(db_path) as conn:
                conn.execute("create table if not exists p0_probe(id integer primary key, created_at text not null)")
                conn.execute("insert into p0_probe(created_at) values (?)", (datetime.now(timezone.utc).isoformat(),))
                conn.commit()
            checks.append(_check("local_sqlite_probe", True, "blocker", {"path": str(db_path)}))
            checks.append(_check("production_database_url_declared", False, "warning", {"expected": "DATABASE_URL or production.database.url"}))
        except Exception as exc:  # pragma: no cover - filesystem boundary
            checks.append(_check("local_sqlite_probe", False, "blocker", {"path": str(db_path), "error": str(exc)}))
    blockers = sum(1 for c in checks if not c["ok"] and c["severity"] == "blocker")
    warnings = sum(1 for c in checks if not c["ok"] and c["severity"] == "warning")
    return {"ok": blockers == 0, "status": "pass" if blockers == 0 else "blocked", "mode": db_mode, "blockers": blockers, "warnings": warnings, "checks": _stable_checks(checks)}


def event_bus_readiness(runtime_dir: str | Path) -> dict[str, Any]:
    bus = EventBus(runtime_dir)
    event = bus.publish("runtime.p0_readiness", "p0_runtime", {"probe": True}, 1)
    status = bus.status()
    checks = [
        _check("event_bus_publish", bool(event.get("event_id")), "blocker", {"event_id": event.get("event_id")}),
        _check("event_bus_status_healthy", bool(status.get("healthy")), "blocker", status),
        _check("event_bus_component_v121", status.get("component") == "event_bus_v121", "blocker", {"component": status.get("component")}),
    ]
    blockers = sum(1 for c in checks if not c["ok"] and c["severity"] == "blocker")
    return {"ok": blockers == 0, "status": "pass" if blockers == 0 else "blocked", "blockers": blockers, "checks": _stable_checks(checks), "event_id": event.get("event_id")}


def runtime_state_readiness(project_root: str | Path, runtime_dir: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    runtime = Path(runtime_dir)
    required_dirs = [runtime, runtime / "reports", runtime / "state", runtime / "events_v121"]
    checks: list[dict[str, Any]] = []
    for directory in required_dirs:
        ok, error = _runtime_writable(directory)
        checks.append(_check(f"writable:{directory.name}", ok, "blocker", {"path": str(directory), "error": error}))
    recovery_file = runtime / "state" / "runtime_recovery.json"
    if not recovery_file.exists():
        recovery_file.write_text(json.dumps({"schema": "secondbrain.runtime_recovery.v1", "created_at": datetime.now(timezone.utc).isoformat(), "project_root": str(root)}, indent=2), encoding="utf-8")
    checks.append(_check("runtime_recovery_file", recovery_file.exists(), "blocker", {"path": str(recovery_file)}))
    blockers = sum(1 for c in checks if not c["ok"] and c["severity"] == "blocker")
    return {"ok": blockers == 0, "status": "pass" if blockers == 0 else "blocked", "blockers": blockers, "checks": _stable_checks(checks)}


def p0_readiness(project_root: str | Path, profile: str | None = None, write_report: bool = False) -> dict[str, Any]:
    root = Path(project_root).resolve()
    config = load_runtime_snapshot(root, profile)
    missing_config = [name for name, present in config.config_files.items() if not present]
    config_checks = [_check("required_config_files", not missing_config, "blocker", {"missing": missing_config, "required": list(REQUIRED_CONFIG_FILES)})]
    secrets = secrets_readiness(root)
    database = database_readiness(root, profile)
    event_bus = event_bus_readiness(config.runtime_dir)
    state = runtime_state_readiness(root, config.runtime_dir)
    checks = config_checks + [
        _check("secrets_readiness", secrets["ok"], "blocker", {"status": secrets["status"], "blockers": secrets["blockers"], "warnings": secrets["warnings"]}),
        _check("database_readiness", database["ok"], "blocker", {"status": database["status"], "mode": database["mode"], "blockers": database["blockers"], "warnings": database["warnings"]}),
        _check("event_bus_readiness", event_bus["ok"], "blocker", {"status": event_bus["status"], "event_id": event_bus.get("event_id")}),
        _check("runtime_state_readiness", state["ok"], "blocker", {"status": state["status"], "blockers": state["blockers"]}),
    ]
    checks = _stable_checks(checks)
    blockers = sum(1 for c in checks if not c["ok"] and c["severity"] == "blocker")
    warnings = secrets["warnings"] + database["warnings"]
    payload = {
        "schema": "secondbrain.p0_readiness.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if blockers == 0 else "blocked",
        "ok": blockers == 0,
        "blockers": blockers,
        "warnings": warnings,
        "checks": checks,
        "config": config.to_dict(),
        "secrets": secrets,
        "database": database,
        "event_bus": event_bus,
        "state": state,
    }
    if write_report:
        payload["report"] = _write_named_report(payload, root, "p0_readiness_latest.json")
    return payload


def p0_bootstrap(project_root: str | Path, profile: str | None = None, write_report: bool = False) -> dict[str, Any]:
    root = Path(project_root).resolve()
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    defaults = {
        "settings.yaml": "runtime_dir: runtime\n",
        "runtime.yaml": "runtime_dir: runtime\n",
        "production.yaml": "enabled: false\ndatabase:\n  pgvector: false\n",
        "security.yaml": "privacy_mode: false\nsecrets:\n  encryption: development-file\n",
        "connectors.yaml": "connectors: []\n",
    }
    created: list[str] = []
    preserved: list[str] = []
    for name, content in defaults.items():
        path = config_dir / name
        if path.exists():
            preserved.append(name)
        else:
            path.write_text(content, encoding="utf-8")
            created.append(name)
    template = config_dir / "secrets.template.yaml"
    if not template.exists():
        template.write_text("# Copy to secrets.yaml locally. Never commit live secrets.\nproviders:\n  openai_api_key: change_me\n", encoding="utf-8")
        created.append("secrets.template.yaml")
    readiness = p0_readiness(root, profile, write_report=write_report)
    payload = {
        "schema": "secondbrain.p0_bootstrap.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if readiness["ok"] else "blocked",
        "ok": readiness["ok"],
        "created": created,
        "preserved": preserved,
        "readiness": {"status": readiness["status"], "blockers": readiness["blockers"], "warnings": readiness["warnings"]},
    }
    if write_report:
        payload["report"] = _write_named_report(payload, root, "p0_bootstrap_latest.json")
    return payload



def p0_artifact_audit(project_root: str | Path, profile: str | None = None, write_report: bool = False) -> dict[str, Any]:
    """Audit local P0 artifacts required for repeatable operation.

    Scope: report directory, latest gate/readiness/smoke/contract reports,
    recovery state, event log, launcher file, and test presence. This is not a
    functional gate for external services; it proves that P0 writes the
    evidence needed by CI, support, and rollback decisions.
    """
    root = Path(project_root).resolve()
    config = load_runtime_snapshot(root, profile)
    runtime = Path(config.runtime_dir)
    reports = runtime / "reports"
    expected_reports = {
        "gate": reports / "p0_gate_latest.json",
        "readiness": reports / "p0_readiness_latest.json",
        "smoke": reports / "p0_smoke_latest.json",
        "contract": reports / "p0_contract_latest.json",
    }
    checks: list[dict[str, Any]] = []
    checks.append(_check("launcher_file_present", (root / "launcher.py").exists(), "blocker", {"path": str(root / "launcher.py")}))
    checks.append(_check("p0_runtime_module_present", (root / "secondbrain" / "p0_runtime.py").exists(), "blocker", {"path": str(root / "secondbrain" / "p0_runtime.py")}))
    checks.append(_check("p0_integration_tests_present", (root / "tests" / "test_v170_p0_integration.py").exists(), "blocker", {"path": str(root / "tests" / "test_v170_p0_integration.py")}))
    checks.append(_check("reports_dir_present", reports.exists(), "blocker", {"path": str(reports)}))
    for key, path in expected_reports.items():
        checks.append(_check(f"report_present:{key}", path.exists(), "warning", {"path": str(path)}))
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                checks.append(_check(f"report_json_valid:{key}", isinstance(data, dict) and bool(data.get("schema")), "blocker", {"schema": data.get("schema")}))
            except Exception as exc:
                checks.append(_check(f"report_json_valid:{key}", False, "blocker", {"error": str(exc)}))
    recovery = runtime / "state" / "runtime_recovery.json"
    events = runtime / "events_v121" / "events.jsonl"
    checks.append(_check("runtime_recovery_present", recovery.exists(), "blocker", {"path": str(recovery)}))
    checks.append(_check("event_log_present", events.exists(), "blocker", {"path": str(events)}))
    if events.exists():
        try:
            line_count = sum(1 for line in events.read_text(encoding="utf-8").splitlines() if line.strip())
            checks.append(_check("event_log_non_empty", line_count > 0, "blocker", {"lines": line_count}))
        except Exception as exc:
            checks.append(_check("event_log_non_empty", False, "blocker", {"error": str(exc)}))
    checks = _stable_checks(checks)
    blockers = sum(1 for c in checks if not c["ok"] and c["severity"] == "blocker")
    warnings = sum(1 for c in checks if not c["ok"] and c["severity"] == "warning")
    payload = {
        "schema": "secondbrain.p0_artifact_audit.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if blockers == 0 else "blocked",
        "ok": blockers == 0,
        "blockers": blockers,
        "warnings": warnings,
        "checks": checks,
        "artifacts": {k: str(v) for k, v in expected_reports.items()},
        "runtime_dir": str(runtime),
    }
    if write_report:
        payload["report"] = _write_named_report(payload, root, "p0_artifact_audit_latest.json")
    return payload


def p0_production_gate(project_root: str | Path, profile: str | None = None, write_report: bool = False) -> dict[str, Any]:
    """Strict P0 production entry gate.

    Requires the full local P0 sequence to pass and persists every report needed
    for CI and operator handover. Production-specific external integrations may
    still emit warnings when no DATABASE_URL or pgvector declaration exists, but
    P0 blocks only on launch/runtime/contract/readiness/audit failures.
    """
    root = Path(project_root).resolve()
    bootstrap = p0_bootstrap(root, profile, write_report=True)
    contract = p0_contract(root, profile, write_report=True)
    readiness = p0_readiness(root, profile, write_report=True)
    gate = p0_gate(root, profile, write_report=True)
    smoke = p0_smoke(root, profile, write_report=True)
    audit = p0_artifact_audit(root, profile, write_report=True)
    checks = [
        _check("bootstrap_passes", bootstrap["ok"], "blocker", {"status": bootstrap["status"], "created": bootstrap.get("created", [])}),
        _check("contract_passes", contract["ok"], "blocker", {"status": contract["status"], "blockers": contract["blockers"]}),
        _check("readiness_passes", readiness["ok"], "blocker", {"status": readiness["status"], "blockers": readiness["blockers"], "warnings": readiness["warnings"]}),
        _check("gate_passes", gate["ok"], "blocker", {"status": gate["status"], "score": gate["score"], "blockers": gate["blockers"]}),
        _check("smoke_passes", smoke["ok"], "blocker", {"status": smoke["status"], "blockers": smoke["blockers"]}),
        _check("artifact_audit_passes", audit["ok"], "blocker", {"status": audit["status"], "blockers": audit["blockers"], "warnings": audit["warnings"]}),
    ]
    checks = _stable_checks(checks)
    blockers = sum(1 for c in checks if not c["ok"] and c["severity"] == "blocker")
    warnings = readiness.get("warnings", 0) + audit.get("warnings", 0)
    score = round(100 * (len(checks) - blockers - (warnings * 0.05)) / len(checks), 1)
    payload = {
        "schema": "secondbrain.p0_production_gate.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if blockers == 0 else "blocked",
        "ok": blockers == 0,
        "score": max(0, score),
        "blockers": blockers,
        "warnings": warnings,
        "checks": checks,
        "sequence": {
            "bootstrap": {"status": bootstrap["status"], "report": bootstrap.get("report")},
            "contract": {"status": contract["status"], "report": contract.get("report")},
            "readiness": {"status": readiness["status"], "report": readiness.get("report"), "warnings": readiness.get("warnings")},
            "gate": {"status": gate["status"], "score": gate.get("score"), "report": gate.get("report")},
            "smoke": {"status": smoke["status"], "report": smoke.get("report")},
            "audit": {"status": audit["status"], "report": audit.get("report")},
        },
    }
    if write_report:
        payload["report"] = _write_named_report(payload, root, "p0_production_gate_latest.json")
    return payload


def p0_contract(project_root: str | Path, profile: str | None = None, write_report: bool = False) -> dict[str, Any]:
    """Validate the P0 public launcher contract without external services.

    Contract scope: public commands must be uniquely owned, critical commands
    must resolve to a registered module, critical modules must expose import
    metadata, and the launcher entrypoint must be present. This prevents the
    regression where one feature branch replaces the launcher surface of older
    modules.
    """
    root = Path(project_root).resolve()
    launcher_path = root / "launcher.py"
    if not launcher_path.exists():
        launcher_path = Path(__file__).resolve().parent.parent / "launcher.py"
    registry = ModuleRegistry()
    command_index = registry.command_index()
    conflicts = registry.command_conflicts()
    missing = [cmd for cmd in CRITICAL_COMMANDS if cmd not in command_index and cmd != "command-index"]
    unresolved = [cmd for cmd in CRITICAL_COMMANDS if registry.resolve_command(cmd) is None]
    critical_without_import = [m["key"] for m in registry.critical_modules() if not m.get("import_path")]
    prefix_coverage: dict[str, bool] = {}
    for module in registry.list():
        for prefix in module.get("command_prefixes", []):
            prefix_coverage[prefix] = any(command.startswith(prefix) or command == prefix.rstrip("-") for command in module.get("commands", []))
    checks = [
        _check("launcher_entrypoint_exists", launcher_path.exists(), "blocker", {"path": str(launcher_path)}),
        _check("critical_commands_declared", not missing, "blocker", {"missing": missing, "required": list(CRITICAL_COMMANDS)}),
        _check("critical_commands_resolve", not unresolved, "blocker", {"unresolved": unresolved}),
        _check("command_index_unique", not conflicts, "blocker", {"conflicts": conflicts}),
        _check("critical_modules_have_import_path", not critical_without_import, "blocker", {"modules": critical_without_import}),
        _check("command_prefixes_have_commands", all(prefix_coverage.values()), "blocker", {"prefixes": prefix_coverage}),
    ]
    checks = _stable_checks(checks)
    blockers = sum(1 for c in checks if not c["ok"] and c["severity"] == "blocker")
    payload = {
        "schema": "secondbrain.p0_contract.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if blockers == 0 else "blocked",
        "ok": blockers == 0,
        "blockers": blockers,
        "checks": checks,
        "contract": {
            "critical_commands": list(CRITICAL_COMMANDS),
            "command_count": len(command_index),
            "modules": registry.keys(),
            "critical_modules": [m["key"] for m in registry.critical_modules()],
        },
    }
    if write_report:
        payload["report"] = _write_named_report(payload, root, "p0_contract_latest.json")
    return payload


def p0_gate(project_root: str | Path, profile: str | None = None, write_report: bool = False) -> dict[str, Any]:
    """Return a strict, machine-readable P0 gate.

    P0 is allowed to pass only when the project can be launched, config can be
    resolved, critical modules can be imported, runtime health succeeds for
    critical modules, and the event/runtime directory is writable.
    """
    root = Path(project_root).resolve()
    registry = ModuleRegistry()
    config = load_runtime_snapshot(root, profile)
    runtime_dir = Path(config.runtime_dir)
    import_health = registry.import_health()
    runtime_health = registry.runtime_health(root, profile)
    missing_config = [name for name, present in config.config_files.items() if not present]
    writable, writable_error = _runtime_writable(runtime_dir)
    command_index = registry.command_index()
    command_conflicts = registry.command_conflicts()
    contract = p0_contract(root, profile)
    readiness = p0_readiness(root, profile)
    missing_commands = [cmd for cmd in CRITICAL_COMMANDS if cmd not in command_index and cmd not in {"command-index"}]
    checks = [
        _check("python_version", sys.version_info >= (3, 11), "blocker", {"version": sys.version.split()[0], "minimum": "3.11"}),
        _check("project_root_exists", root.exists(), "blocker", {"path": str(root)}),
        _check("required_config_files", not missing_config, "blocker", {"missing": missing_config, "required": list(REQUIRED_CONFIG_FILES)}),
        _check("runtime_dir_writable", writable, "blocker", {"path": str(runtime_dir), "error": writable_error}),
        _check("critical_import_health", bool(import_health.get("ok")), "blocker", import_health),
        _check("critical_runtime_health", bool(runtime_health.get("ok")), "blocker", runtime_health),
        _check("critical_command_index", not missing_commands, "blocker", {"missing": missing_commands, "available": sorted(command_index)}),
        _check("command_index_unique", not command_conflicts, "blocker", {"conflicts": command_conflicts}),
        _check("p0_launcher_contract", bool(contract.get("ok")), "blocker", {"status": contract.get("status"), "blockers": contract.get("blockers")}),
        _check("p0_runtime_readiness", bool(readiness.get("ok")), "blocker", {"status": readiness.get("status"), "blockers": readiness.get("blockers"), "warnings": readiness.get("warnings")}),
    ]
    blocker_count = sum(1 for c in checks if not c["ok"] and c["severity"] == "blocker")
    warning_count = sum(1 for c in checks if not c["ok"] and c["severity"] == "warning")
    status = "pass" if blocker_count == 0 else "blocked"
    payload = {
        "schema": "secondbrain.p0_gate.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "ok": status == "pass",
        "score": round(100 * (len(checks) - blocker_count - (warning_count * 0.25)) / len(checks), 1),
        "blockers": blocker_count,
        "warnings": warning_count,
        "checks": checks,
        "config": config.to_dict(),
        "registry": {"modules": registry.keys(), "critical_modules": [m["key"] for m in registry.critical_modules()], "commands": len(command_index), "command_conflicts": command_conflicts},
        "contract": {"status": contract["status"], "blockers": contract["blockers"]},
        "readiness": {"status": readiness["status"], "blockers": readiness["blockers"], "warnings": readiness["warnings"]},
        "environment": {"cwd": os.getcwd(), "executable": sys.executable},
    }
    payload["checks"] = _stable_checks(payload["checks"])
    if write_report:
        payload["report"] = write_p0_report(payload, root)
    return payload


def p0_report(project_root: str | Path, profile: str | None = None) -> dict[str, Any]:
    payload = p0_gate(project_root, profile, write_report=True)
    return {"status": payload["status"], "ok": payload["ok"], "score": payload["score"], "blockers": payload["blockers"], "warnings": payload["warnings"], "report": payload.get("report")}


def p0_smoke(project_root: str | Path, profile: str | None = None, write_report: bool = False) -> dict[str, Any]:
    """Run a lightweight P0 smoke suite without external services.

    Scope: launcher-critical module imports, runtime status methods, config
    resolution, event bus write path, command index uniqueness, and report
    persistence. It intentionally avoids network, OAuth, LLM calls, and GUI
    startup.
    """
    root = Path(project_root).resolve()
    registry = ModuleRegistry()
    config = load_runtime_snapshot(root, profile)
    bus = EventBus(config.runtime_dir)
    event = bus.publish(
        "runtime.p0_smoke",
        "p0_runtime",
        {"project_root": str(root), "profile": config.profile},
        1,
    )
    gate = p0_gate(root, profile, write_report=write_report)
    contract = p0_contract(root, profile, write_report=write_report)
    readiness = p0_readiness(root, profile, write_report=write_report)
    checks = [
        _check("gate_passes", gate["ok"], "blocker", {"status": gate["status"], "score": gate["score"], "blockers": gate["blockers"]}),
        _check("event_bus_publish", bool(event.get("event_id")), "blocker", {"event_id": event.get("event_id"), "status": bus.status()}),
        _check("critical_modules_declared", bool(registry.critical_modules()), "blocker", {"critical_modules": [m["key"] for m in registry.critical_modules()]}),
        _check("command_resolution_core", registry.resolve_command("health") is not None, "blocker", {"command": "health"}),
        _check("command_resolution_desktop", registry.resolve_command("desktop-status") is not None, "blocker", {"command": "desktop-status"}),
        _check("command_resolution_mobile", registry.resolve_command("mobile16-status") is not None, "blocker", {"command": "mobile16-status"}),
        _check("contract_passes", contract["ok"], "blocker", {"status": contract["status"], "blockers": contract["blockers"]}),
        _check("readiness_passes", readiness["ok"], "blocker", {"status": readiness["status"], "blockers": readiness["blockers"], "warnings": readiness["warnings"]}),
    ]
    checks = _stable_checks(checks)
    blockers = sum(1 for c in checks if not c["ok"] and c["severity"] == "blocker")
    payload = {
        "schema": "secondbrain.p0_smoke.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "pass" if blockers == 0 else "blocked",
        "ok": blockers == 0,
        "blockers": blockers,
        "checks": checks,
        "gate": {"status": gate["status"], "score": gate["score"], "blockers": gate["blockers"], "warnings": gate["warnings"]},
        "contract": {"status": contract["status"], "blockers": contract["blockers"]},
        "readiness": {"status": readiness["status"], "blockers": readiness["blockers"], "warnings": readiness["warnings"]},
        "event_id": event.get("event_id"),
    }
    if write_report:
        reports_dir = root / "runtime" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        smoke_path = reports_dir / "p0_smoke_latest.json"
        smoke_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        payload["report"] = {"path": str(smoke_path), "bytes": smoke_path.stat().st_size}
    return payload


def p0_doctor(project_root: str | Path, profile: str | None = None) -> dict[str, Any]:
    root = Path(project_root).resolve()
    registry = ModuleRegistry()
    config = load_runtime_snapshot(root, profile)
    bus = EventBus(config.runtime_dir)
    marker = bus.publish(
        "runtime.p0_doctor",
        "p0_runtime",
        {"project_root": str(root), "profile": config.profile, "modules": registry.keys()},
        1,
    )
    import_health = registry.import_health()
    runtime_health = registry.runtime_health(root, profile)
    gate = p0_gate(root, profile, write_report=True)
    contract = p0_contract(root, profile)
    readiness = p0_readiness(root, profile)
    return {
        "status": "ok" if gate["ok"] else "degraded",
        "ok": gate["ok"],
        "config": config.to_dict(),
        "registry": {"modules": registry.keys(), "commands": len(registry.command_index())},
        "import_health": import_health,
        "runtime_health": runtime_health,
        "event_bus": bus.status(),
        "doctor_event_id": marker.get("event_id"),
        "missing_config": [name for name, present in config.config_files.items() if not present],
        "gate": {"status": gate["status"], "score": gate["score"], "blockers": gate["blockers"], "warnings": gate["warnings"]},
        "contract": {"status": contract["status"], "blockers": contract["blockers"]},
        "readiness": {"status": readiness["status"], "blockers": readiness["blockers"], "warnings": readiness["warnings"]},
    }
