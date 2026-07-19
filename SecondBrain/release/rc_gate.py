"""Release-candidate gate for v30.80.

Runs a fixed set of readiness checks and produces a single verdict:
- BLOCKED           : at least one FAIL (or a hard-rule violation)
- CONDITIONAL_PASS  : no FAIL, but at least one WARN
- PASS              : everything green

Hard rules (never PASS/CONDITIONAL_PASS when violated -> always BLOCKED):
- embeddings must not be DEV_ONLY/deterministic in a production build
- the Secret Vault must be importable and healthy
- a Connector Runtime must be defined

Every non-PASS check records file, cause, and remediation so blockers are
actionable. Checks that require the full 3.11 launcher runtime degrade to WARN
with an explicit "verify under 3.11" note instead of silently passing.
"""

from __future__ import annotations

import importlib
import importlib.util
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable


class CheckStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


class Verdict(str, Enum):
    PASS = "PASS"
    CONDITIONAL_PASS = "CONDITIONAL_PASS"
    BLOCKED = "BLOCKED"


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    summary: str
    critical: bool = False
    file: str | None = None
    cause: str | None = None
    remediation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "summary": self.summary,
            "critical": self.critical,
            "file": self.file,
            "cause": self.cause,
            "remediation": self.remediation,
        }


@dataclass
class GateContext:
    project_root: Path
    target_version: str
    checks_run: list[str] = field(default_factory=list)


def _module_exists(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


# --- individual checks ---------------------------------------------------------

def check_version_sync(ctx: GateContext) -> CheckResult:
    try:
        from secondbrain.version import get_version
        current = get_version()
    except Exception as exc:  # noqa: BLE001
        return CheckResult("version_sync", CheckStatus.FAIL, "version not readable",
                           file="secondbrain/version.py", cause=str(exc),
                           remediation="repair secondbrain/version.py / pyproject.toml")
    if current != ctx.target_version:
        return CheckResult("version_sync", CheckStatus.WARN,
                           f"pyproject version {current} != RC target {ctx.target_version}",
                           file="pyproject.toml", cause="version not bumped to the RC target",
                           remediation=f"set [project].version = {ctx.target_version} before tagging")
    return CheckResult("version_sync", CheckStatus.PASS, f"version {current} consistent")


def check_repo_doctor(ctx: GateContext) -> CheckResult:
    required = ["pyproject.toml", "launcher.py", "SecondBrain"]
    missing = [r for r in required if not (ctx.project_root / r).exists()]
    if missing:
        return CheckResult("repo_doctor", CheckStatus.FAIL, "core repo files missing",
                           file=", ".join(missing), cause="incomplete checkout",
                           remediation="restore missing paths from version control")
    return CheckResult("repo_doctor", CheckStatus.WARN, "structural check only",
                       cause="full repo doctor requires the 3.11 launcher runtime",
                       remediation="run `launcher.py doctor` under Python 3.11 for the authoritative result")


def check_dependency_inventory(ctx: GateContext) -> CheckResult:
    if not _module_exists("cryptography"):
        return CheckResult("dependency_inventory", CheckStatus.FAIL, "cryptography missing",
                           file="requirements-security.txt", cause="Secret Vault dependency not installed",
                           remediation="pip install -r requirements-security.txt")
    reqs = list(ctx.project_root.glob("requirements*.txt"))
    if not reqs:
        return CheckResult("dependency_inventory", CheckStatus.FAIL, "no requirements files",
                           file="requirements*.txt", cause="dependency manifests missing",
                           remediation="restore requirements files")
    return CheckResult("dependency_inventory", CheckStatus.PASS,
                       f"{len(reqs)} requirement manifests, core deps present")


def check_pgvector_readiness(ctx: GateContext) -> CheckResult:
    if _module_exists("psycopg") or _module_exists("psycopg2"):
        return CheckResult("pgvector_readiness", CheckStatus.PASS, "postgres driver available")
    return CheckResult("pgvector_readiness", CheckStatus.WARN, "no postgres driver installed",
                       file="requirements-db.txt", cause="psycopg not installed in this environment",
                       remediation="pip install -r requirements-db.txt and configure DATABASE_URL for the pgvector backend")


def check_embedding_provider(ctx: GateContext) -> CheckResult:
    """HARD RULE: DEV_ONLY/deterministic embeddings must never pass."""
    try:
        from secondbrain.p1_embedding_config import evaluate_embedding_config
        health = evaluate_embedding_config(ctx.project_root, production=True)
        blockers = health.get("blockers", [])
        provider = health.get("provider") or health.get("config", {}).get("provider")
    except Exception as exc:  # noqa: BLE001
        return CheckResult("embedding_provider", CheckStatus.FAIL, "embedding config not evaluable",
                           critical=True, file="secondbrain/p1_embedding_config.py", cause=str(exc),
                           remediation="fix the embedding configuration evaluation")
    if blockers:
        return CheckResult("embedding_provider", CheckStatus.FAIL,
                           f"embedding not production-ready (provider={provider})",
                           critical=True, file=".env / config embedding profile",
                           cause="; ".join(blockers),
                           remediation="configure a semantic provider (openai/ollama) with a passing health probe; "
                                       "DEV_ONLY/deterministic embeddings are not allowed for a release")
    return CheckResult("embedding_provider", CheckStatus.PASS, f"production embedding provider {provider}")


def check_secret_vault(ctx: GateContext) -> CheckResult:
    """HARD RULE: a working Secret Vault is required."""
    if not _module_exists("secondbrain.vault"):
        return CheckResult("secret_vault", CheckStatus.FAIL, "secret vault package missing",
                           critical=True, file="secondbrain/vault/", cause="vault package not importable",
                           remediation="ship the secondbrain.vault package")
    try:
        import tempfile
        from secondbrain.vault import crypto
        from secondbrain.vault.health import health_check
        from secondbrain.vault.store import SecretVault
        tmp = tempfile.mkdtemp()
        vault = SecretVault(tmp, env={"SECONDBRAIN_VAULT_KEY": crypto.b64e(crypto.new_key())})
        vault.put_secret("rc_probe", "value", workspace="rc")
        report = health_check(vault)
    except Exception as exc:  # noqa: BLE001
        return CheckResult("secret_vault", CheckStatus.FAIL, "vault self-test failed", critical=True,
                           file="secondbrain/vault/", cause=str(exc),
                           remediation="repair the vault crypto/store path")
    if not report.get("ok"):
        return CheckResult("secret_vault", CheckStatus.FAIL, "vault health failed", critical=True,
                           file="secondbrain/vault/health.py", cause=str(report.get("blockers")),
                           remediation="resolve vault health blockers")
    return CheckResult("secret_vault", CheckStatus.PASS, "vault encrypt/health self-test passed")


def check_connector_runtime(ctx: GateContext) -> CheckResult:
    """HARD RULE: a Connector Runtime must be defined."""
    if not _module_exists("secondbrain.connector_runtime"):
        return CheckResult("connector_runtime", CheckStatus.FAIL, "connector runtime missing", critical=True,
                           file="secondbrain/connector_runtime/", cause="package not importable",
                           remediation="ship the secondbrain.connector_runtime package")
    try:
        from secondbrain.connector_runtime import ConnectorRuntime, LocalFolderConnector  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        return CheckResult("connector_runtime", CheckStatus.FAIL, "connector runtime broken", critical=True,
                           file="secondbrain/connector_runtime/", cause=str(exc),
                           remediation="repair the connector runtime imports")
    return CheckResult("connector_runtime", CheckStatus.PASS, "connector runtime defined (registry + connectors)")


def _structural(ctx: GateContext, name: str, path: str, label: str) -> CheckResult:
    """Filesystem-based presence check.

    We check the path on disk rather than importing, because the full package
    imports require the 3.11 launcher runtime; import-probing under an older
    interpreter would produce false negatives. Present -> WARN (verify at runtime),
    missing -> FAIL.
    """
    if not (ctx.project_root / path).exists():
        return CheckResult(name, CheckStatus.FAIL, f"{label} missing", file=path,
                           cause="path not found on disk", remediation=f"restore {path}")
    return CheckResult(name, CheckStatus.WARN, f"{label} present (not runtime-verified)",
                       file=path, cause="runtime verification requires the 3.11 launcher",
                       remediation=f"verify {name} under Python 3.11 before tagging")


def check_native_desktop(ctx: GateContext) -> CheckResult:
    return _structural(ctx, "native_desktop", "SecondBrain/native", "native desktop package")


def check_agent_safety(ctx: GateContext) -> CheckResult:
    return _structural(ctx, "agent_safety", "SecondBrain/agent/safety", "agent safety package")


def check_workflow_engine(ctx: GateContext) -> CheckResult:
    return _structural(ctx, "workflow_engine", "SecondBrain/agent/workflow", "workflow engine package")


def check_memory_injection(ctx: GateContext) -> CheckResult:
    return _structural(ctx, "memory_injection", "SecondBrain/agent/memory_injection", "memory injection package")


def check_scheduler(ctx: GateContext) -> CheckResult:
    for path in ("SecondBrain/agent/background_agents", "SecondBrain/scheduler.py"):
        if (ctx.project_root / path).exists():
            return _structural(ctx, "scheduler", path, "scheduler / background-agent runtime")
    return CheckResult("scheduler", CheckStatus.WARN, "no scheduler module found",
                       file="SecondBrain/agent/background_agents/", cause="scheduler module not located",
                       remediation="confirm the scheduler/background-agent runtime is shipped")


def check_plugin_runtime(ctx: GateContext) -> CheckResult:
    manifest = ctx.project_root / "plugin_manifest.json"
    if manifest.exists():
        return CheckResult("plugin_runtime", CheckStatus.PASS, "plugin manifest present")
    return CheckResult("plugin_runtime", CheckStatus.WARN, "no plugin manifest",
                       file="plugin_manifest.json", cause="plugin manifest not found",
                       remediation="ship plugin_manifest.json if the plugin runtime is in scope")


def check_installer_build(ctx: GateContext) -> CheckResult:
    needed = ["packaging/windows/jarvis.spec", "packaging/windows/installer.iss",
              "packaging/windows/build.ps1", "packaging/windows/jarvis_bootstrap.py",
              "SecondBrain/install/__init__.py"]
    missing = [n for n in needed if not (ctx.project_root / n).exists()]
    if missing:
        return CheckResult("installer_build", CheckStatus.FAIL, "installer assets missing",
                           file=", ".join(missing), cause="incomplete Windows packaging",
                           remediation="restore the packaging/windows assets and SecondBrain.install package")
    return CheckResult("installer_build", CheckStatus.WARN, "installer assets present (not built here)",
                       file="packaging/windows/", cause="PyInstaller/Inno build requires Windows + Python 3.11",
                       remediation="run packaging/windows/build.ps1 on Windows and attach the artifacts")


def check_pytest(ctx: GateContext) -> CheckResult:
    if not _module_exists("pytest"):
        return CheckResult("pytest", CheckStatus.FAIL, "pytest not installed",
                           file="requirements-dev.txt", cause="test runner missing",
                           remediation="pip install pytest")
    return CheckResult("pytest", CheckStatus.WARN, "full suite not executed by the gate",
                       file="tests/", cause="the complete suite (incl. launcher tests) requires Python 3.11",
                       remediation="run `pytest` under Python 3.11 and attach the summary before tagging")


DEFAULT_CHECKS: list[Callable[[GateContext], CheckResult]] = [
    check_version_sync, check_repo_doctor, check_dependency_inventory, check_pgvector_readiness,
    check_embedding_provider, check_secret_vault, check_connector_runtime, check_native_desktop,
    check_agent_safety, check_workflow_engine, check_memory_injection, check_scheduler,
    check_plugin_runtime, check_installer_build, check_pytest,
]


def decide_verdict(results: list[CheckResult]) -> Verdict:
    if any(r.status is CheckStatus.FAIL for r in results):
        return Verdict.BLOCKED
    if any(r.status is CheckStatus.WARN for r in results):
        return Verdict.CONDITIONAL_PASS
    return Verdict.PASS


def run_rc_gate(project_root: str | Path = ".", *, target_version: str | None = None,
                checks: list[Callable[[GateContext], CheckResult]] | None = None) -> dict[str, Any]:
    if target_version is None:
        from secondbrain.version import get_version
        target_version = get_version()
    ctx = GateContext(project_root=Path(project_root), target_version=target_version)
    results = [fn(ctx) for fn in (checks or DEFAULT_CHECKS)]
    verdict = decide_verdict(results)
    blockers = [r.to_dict() for r in results if r.status is CheckStatus.FAIL]
    warnings = [r.to_dict() for r in results if r.status is CheckStatus.WARN]
    return {
        "schema": "secondbrain.rc_gate.v1",
        "target_version": target_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict.value,
        "summary": {
            "pass": sum(1 for r in results if r.status is CheckStatus.PASS),
            "warn": len(warnings),
            "fail": len(blockers),
            "total": len(results),
        },
        "checks": [r.to_dict() for r in results],
        "blockers": blockers,
        "warnings": warnings,
    }


def write_artifacts(report: dict[str, Any], project_root: str | Path = ".") -> dict[str, str]:
    root = Path(project_root)
    json_path = root / "release" / "rc_status_latest.json"
    md_path = root / "docs" / "releases" / "v30_80_rc_report.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    import json
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def _render_markdown(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines = [
        f"# Release-Candidate-Report v{report['target_version']}",
        "",
        f"Bewertung: **{report['verdict']}**  ",
        f"Erzeugt: {report['generated_at']}  ",
        f"Checks: {s['pass']} PASS / {s['warn']} WARN / {s['fail']} FAIL (gesamt {s['total']})",
        "",
        "## Bewertungsregel",
        "",
        "BLOCKED bei mindestens einem FAIL; CONDITIONAL_PASS bei WARN ohne FAIL; sonst PASS. "
        "Hartregeln erzwingen BLOCKED: DEV_ONLY-Embeddings, fehlender Secret Vault, fehlende Connector Runtime.",
        "",
        "## CheckÃ¼bersicht",
        "",
        "| Check | Status | Kritisch | Zusammenfassung |",
        "|-------|--------|----------|-----------------|",
    ]
    for c in report["checks"]:
        lines.append(f"| {c['name']} | {c['status'].upper()} | {'ja' if c['critical'] else '-'} | {c['summary']} |")

    if report["blockers"]:
        lines += ["", "## Blocker (Datei / Ursache / MaÃŸnahme)", ""]
        for b in report["blockers"]:
            lines += [
                f"### {b['name']}" + ("  (Hartregel)" if b["critical"] else ""),
                f"- Datei: `{b['file']}`",
                f"- Ursache: {b['cause']}",
                f"- MaÃŸnahme: {b['remediation']}",
                "",
            ]

    if report["warnings"]:
        lines += ["## Bedingungen (WARN)", ""]
        for w in report["warnings"]:
            loc = f" (`{w['file']}`)" if w["file"] else ""
            lines.append(f"- **{w['name']}**{loc}: {w['summary']} â€” {w['remediation'] or ''}")
        lines.append("")

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    import argparse
    import sys
    parser = argparse.ArgumentParser(prog="secondbrain rc-gate")
    parser.add_argument("project_root", nargs="?", default=".")
    parser.add_argument("--target-version", default=None)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    report = run_rc_gate(args.project_root, target_version=args.target_version)
    paths = write_artifacts(report, args.project_root)
    sys.stdout.write(f"verdict={report['verdict']} -> {paths['json']} / {paths['markdown']}\n")
    return 0 if report["verdict"] != Verdict.BLOCKED.value else 2


if __name__ == "__main__":
    raise SystemExit(main())
