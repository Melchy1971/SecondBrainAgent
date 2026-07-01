from __future__ import annotations

import json
import os
import socket
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


VERSION = "30.21"
DEFAULT_ENV = {
    "SECONDBRAIN_PROFILE": "default",
    "SECONDBRAIN_EMBEDDING_PROVIDER": "local",
    "SECONDBRAIN_EMBEDDING_MODEL": "deterministic-local",
    "SECONDBRAIN_EMBEDDING_DIMENSIONS": "64",
    "SECONDBRAIN_GUI_HOST": "127.0.0.1",
    "SECONDBRAIN_GUI_PORT": "8851",
}
RUNTIME_DIRS = [
    "runtime",
    "runtime/logs",
    "runtime/reports",
    "runtime/jobs",
    "runtime/cache",
    "data",
    "data/p1_rag",
    "SecondBrain-Inbox",
]


@dataclass(frozen=True)
class BootstrapCheck:
    name: str
    ok: bool
    severity: str
    detail: str
    repaired: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def project_root(root: str | Path | None = None) -> Path:
    return Path(root or Path.cwd()).resolve()


def env_path(root: str | Path | None = None) -> Path:
    return project_root(root) / ".env"


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _write_env_file(path: Path, values: dict[str, str]) -> None:
    body = ["# SecondBrain Agent local configuration", "# generated/updated by v30.21 bootstrap"]
    for key in sorted(values):
        body.append(f"{key}={values[key]}")
    path.write_text("\n".join(body) + "\n", encoding="utf-8")


def ensure_env(root: str | Path | None = None, *, repair: bool = True) -> dict[str, Any]:
    path = env_path(root)
    existing = _read_env_file(path)
    merged = dict(DEFAULT_ENV)
    merged.update(existing)
    missing = [key for key in DEFAULT_ENV if key not in existing]
    repaired = False
    if repair and (missing or not path.exists()):
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_env_file(path, merged)
        repaired = True
    return {"ok": path.exists(), "path": str(path), "missing_defaults": missing, "repaired": repaired, "values": merged}


def _can_write(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            prefix=".write_probe_",
            dir=path,
            delete=True,
        ) as probe:
            probe.write("ok")
            probe.flush()
        return True
    except OSError:
        return False


def ensure_runtime_dirs(root: str | Path | None = None, *, repair: bool = True) -> dict[str, Any]:
    base = project_root(root)
    created: list[str] = []
    checks: list[dict[str, Any]] = []
    for rel in RUNTIME_DIRS:
        path = base / rel
        existed = path.exists()
        if repair:
            path.mkdir(parents=True, exist_ok=True)
        ok = path.exists() and path.is_dir()
        if ok and not existed:
            created.append(rel)
        checks.append({"path": rel, "ok": ok, "writable": _can_write(path) if ok else False})
    return {"ok": all(c["ok"] and c["writable"] for c in checks), "created": created, "checks": checks}


def _port_open(host: str, port: int, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _check_database(env: dict[str, str]) -> BootstrapCheck:
    dsn = env.get("DATABASE_URL", "")
    if not dsn:
        return BootstrapCheck("database_url", True, "warning", "DATABASE_URL fehlt; lokaler SQLite/RAG-Prototyp bleibt aktiv")
    if dsn.startswith(("postgresql://", "postgres://")):
        return BootstrapCheck("database_url", True, "info", "PostgreSQL DSN konfiguriert")
    return BootstrapCheck("database_url", False, "blocker", "DATABASE_URL ist kein PostgreSQL DSN")


def _check_embeddings(env: dict[str, str]) -> BootstrapCheck:
    provider = env.get("SECONDBRAIN_EMBEDDING_PROVIDER", "local").strip().lower()
    if provider == "local":
        return BootstrapCheck("embeddings", True, "warning", "lokaler Test-Provider aktiv; Production Gate bleibt blockiert")
    if provider == "openai":
        key_env = env.get("SECONDBRAIN_OPENAI_API_KEY_ENV", "OPENAI_API_KEY")
        if os.environ.get(key_env):
            return BootstrapCheck("embeddings", True, "info", f"OpenAI Provider konfiguriert über {key_env}")
        return BootstrapCheck("embeddings", False, "blocker", f"OpenAI Provider aktiv, aber {key_env} fehlt")
    if provider == "ollama":
        host = env.get("SECONDBRAIN_OLLAMA_HOST", "127.0.0.1")
        port = int(env.get("SECONDBRAIN_OLLAMA_PORT", "11434"))
        ok = _port_open(host, port)
        return BootstrapCheck("embeddings", ok, "info" if ok else "warning", "Ollama erreichbar" if ok else f"Ollama nicht erreichbar: {host}:{port}")
    return BootstrapCheck("embeddings", False, "blocker", f"unbekannter Embedding Provider: {provider}")


def bootstrap_status(root: str | Path | None = None, *, repair: bool = False) -> dict[str, Any]:
    base = project_root(root)
    env_result = ensure_env(base, repair=repair)
    dirs_result = ensure_runtime_dirs(base, repair=repair)
    env = dict(env_result["values"])
    env.update({k: v for k, v in os.environ.items() if k.startswith("SECONDBRAIN_") or k in {"DATABASE_URL", "OPENAI_API_KEY"}})
    checks = [
        BootstrapCheck("python", sys.version_info >= (3, 10), "blocker", sys.version.split()[0]),
        BootstrapCheck("project_root", (base / "launcher.py").exists(), "blocker", str(base)),
        BootstrapCheck("env_file", env_result["ok"], "warning", env_result["path"], repaired=env_result["repaired"]),
        BootstrapCheck("runtime_dirs", dirs_result["ok"], "blocker", "Runtime-/Datenordner vorhanden und beschreibbar", repaired=bool(dirs_result["created"])),
        _check_database(env),
        _check_embeddings(env),
    ]
    blockers = [c.to_dict() for c in checks if not c.ok and c.severity == "blocker"]
    warnings = [c.to_dict() for c in checks if c.severity == "warning"]
    return {
        "ok": not blockers,
        "status": "ready" if not blockers else "blocked",
        "schema": "secondbrain.bootstrap.v1",
        "version": VERSION,
        "project_root": str(base),
        "checks": [c.to_dict() for c in checks],
        "blockers": blockers,
        "warnings": warnings,
        "env": {k: env.get(k) for k in sorted(DEFAULT_ENV)},
        "runtime_dirs": dirs_result,
    }


def bootstrap_text(root: str | Path | None = None, *, repair: bool = True) -> str:
    payload = bootstrap_status(root, repair=repair)
    icons = {True: "OK", False: "FAIL"}
    lines = [f"SecondBrain Agent / Jarvis v{VERSION}", f"Status: {payload['status'].upper()}", ""]
    for check in payload["checks"]:
        suffix = " repaired" if check.get("repaired") else ""
        lines.append(f"[{icons[bool(check['ok'])]}] {check['name']}: {check['detail']}{suffix}")
    return "\n".join(lines)


def write_bootstrap_report(root: str | Path | None = None, *, repair: bool = True) -> dict[str, Any]:
    base = project_root(root)
    payload = bootstrap_status(base, repair=repair)
    report_path = base / "runtime" / "reports" / "bootstrap_v30_21.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    payload["report_path"] = str(report_path)
    return payload
