"""Support bundle: collects diagnostics into a single redacted structure/ZIP.

Every section is defensive (never raises) and every value is passed through the
redactor before it is stored, so the exported ZIP is safe to send to support.
Repository modules are imported lazily/optionally so the bundle also works on a
minimal checkout.
"""

from __future__ import annotations

import json
import os
import platform
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from secondbrain.support import redaction

try:
    import psutil

    _HAS_PSUTIL = True
except Exception:  # noqa: BLE001
    psutil = None  # type: ignore
    _HAS_PSUTIL = False

__all__ = ["SupportBundle", "SECTIONS"]

SCHEMA = "secondbrain.support.bundle.v1"
SECTIONS = [
    "diagnose", "health_snapshot", "config_snapshot", "runtime_snapshot",
    "crash_report", "logs", "system_info", "provider_status", "database_status",
]
_MAX_LOG_BYTES = 64 * 1024


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class SupportBundle:
    def __init__(self, project_root: str | Path = ".") -> None:
        self.root = Path(project_root).resolve()

    # -- public -----------------------------------------------------------

    def collect(self) -> dict[str, Any]:
        sections = {
            "diagnose": self._diagnose(),
            "health_snapshot": self._health_snapshot(),
            "config_snapshot": self._config_snapshot(),
            "runtime_snapshot": self._runtime_snapshot(),
            "crash_report": self._crash_report(),
            "logs": self._logs(),
            "system_info": self._system_info(),
            "provider_status": self._provider_status(),
            "database_status": self._database_status(),
        }
        bundle = {
            "schema": SCHEMA,
            "generated_at": _utc_now(),
            "project_root": str(self.root),
            "sections": sections,
        }
        # Final safety net: redact the whole structure once more.
        return redaction.redact(bundle)

    def build_zip(self, out_path: str | Path, *, bundle: dict[str, Any] | None = None) -> str:
        bundle = bundle if bundle is not None else self.collect()
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("support_bundle.json", json.dumps(bundle, ensure_ascii=False, indent=2))
            for name, section in bundle["sections"].items():
                zf.writestr(f"sections/{name}.json", json.dumps(section, ensure_ascii=False, indent=2))
            logs = bundle["sections"].get("logs", {})
            if isinstance(logs, dict):
                for fname, content in logs.get("files", {}).items():
                    safe = str(fname).replace("/", "_").replace("\\", "_")
                    zf.writestr(f"logs/{safe}", str(content))
        return str(out)

    # -- sections (defensive) ---------------------------------------------

    def _safe(self, fn) -> dict[str, Any]:
        try:
            return {"ok": True, **fn()}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    def _diagnose(self) -> dict[str, Any]:
        def run():
            checks = {
                "project_root_exists": self.root.exists(),
                "runtime_dir": (self.root / "runtime").exists(),
                "config_dir": (self.root / "config").exists(),
                "launcher": (self.root / "launcher.py").exists(),
                "python": sys.version.split()[0],
                "psutil": _HAS_PSUTIL,
            }
            missing = [k for k, v in checks.items() if v is False]
            return {"checks": checks, "status": "ok" if not missing else "degraded", "missing": missing}
        return self._safe(run)

    def _health_snapshot(self) -> dict[str, Any]:
        def run():
            if not _HAS_PSUTIL:
                return {"psutil": False, "note": "psutil nicht installiert"}
            vm = psutil.virtual_memory()
            try:
                du = psutil.disk_usage(str(self.root))
            except Exception:  # noqa: BLE001
                du = psutil.disk_usage("/")
            return {
                "psutil": True,
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "ram_percent": vm.percent,
                "disk_percent": du.percent,
                "ram_total_gb": round(vm.total / 1e9, 2),
                "disk_free_gb": round(du.free / 1e9, 2),
            }
        return self._safe(run)

    def _config_snapshot(self) -> dict[str, Any]:
        def run():
            cfg_dir = self.root / "config"
            files: dict[str, str] = {}
            if cfg_dir.exists():
                for p in sorted(cfg_dir.rglob("*")):
                    if p.is_file() and p.suffix.lower() in {".yaml", ".yml", ".json", ".toml", ".ini", ".env"}:
                        rel = str(p.relative_to(cfg_dir))
                        try:
                            files[rel] = redaction.redact_text(p.read_text(encoding="utf-8", errors="replace")[:_MAX_LOG_BYTES])
                        except OSError:
                            files[rel] = "[unlesbar]"
            return {"config_files": sorted(files), "count": len(files), "contents": files}
        return self._safe(run)

    def _runtime_snapshot(self) -> dict[str, Any]:
        def run():
            try:
                from secondbrain.native.runtime_snapshot import build_native_view_model

                vm = build_native_view_model(self.root)
                keep = {k: vm.get(k) for k in ("schema", "version", "ok", "mode", "bootstrap", "production", "inbox_summary")}
                return {"source": "native_view_model", **keep}
            except Exception as exc:  # noqa: BLE001
                return {"source": "minimal", "note": f"view model nicht verfuegbar: {type(exc).__name__}",
                        "runtime_dir_files": [p.name for p in (self.root / "runtime").glob("*")][:50] if (self.root / "runtime").exists() else []}
        return self._safe(run)

    def _crash_report(self) -> dict[str, Any]:
        def run():
            patterns = ["*crash*.log", "*error*.log", "*.crash", "traceback*.txt"]
            hits: list[dict[str, Any]] = []
            for base in (self.root / "runtime", self.root / "logs", self.root):
                if not base.exists():
                    continue
                for pat in patterns:
                    for p in list(base.rglob(pat))[:10]:
                        if p.is_file():
                            try:
                                tail = p.read_text(encoding="utf-8", errors="replace")[-4096:]
                            except OSError:
                                tail = ""
                            hits.append({"file": str(p.relative_to(self.root)), "tail": redaction.redact_text(tail)})
            return {"crashes": hits[:20], "count": len(hits)}
        return self._safe(run)

    def _logs(self) -> dict[str, Any]:
        def run():
            files: dict[str, str] = {}
            for base in (self.root / "runtime", self.root / "logs"):
                if not base.exists():
                    continue
                for p in sorted(base.rglob("*.log"))[:15]:
                    if p.is_file():
                        try:
                            content = p.read_text(encoding="utf-8", errors="replace")[-_MAX_LOG_BYTES:]
                        except OSError:
                            content = ""
                        files[str(p.relative_to(self.root))] = redaction.redact_text(content)
            return {"files": files, "count": len(files)}
        return self._safe(run)

    def _system_info(self) -> dict[str, Any]:
        def run():
            info = {
                "platform": platform.platform(),
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "python": sys.version.split()[0],
                "executable": sys.executable,
                "cwd": os.getcwd(),
            }
            if _HAS_PSUTIL:
                info["cpu_count"] = psutil.cpu_count()
                info["ram_total_gb"] = round(psutil.virtual_memory().total / 1e9, 2)
            info["env"] = redaction.redact_env(dict(os.environ))
            return info
        return self._safe(run)

    def _provider_status(self) -> dict[str, Any]:
        def run():
            providers = {
                "OpenAI": bool(os.environ.get("OPENAI_API_KEY")),
                "Ollama": bool(os.environ.get("OLLAMA_HOST")),
                "Gemini": bool(os.environ.get("GEMINI_API_KEY")),
                "Anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
            }
            configured = [name for name, present in providers.items() if present]
            embedding = os.environ.get("SECONDBRAIN_EMBEDDING_PROVIDER", "")
            return {"configured": configured, "available_flags": providers, "embedding_provider": embedding}
        return self._safe(run)

    def _database_status(self) -> dict[str, Any]:
        def run():
            dsn = os.environ.get("DATABASE_URL") or os.environ.get("SECONDBRAIN_DATABASE_URL") or ""
            dialect = "unknown"
            if dsn:
                dialect = dsn.split("://", 1)[0] if "://" in dsn else "unknown"
            return {
                "configured": bool(dsn),
                "dialect": dialect,
                "dsn": redaction.redact_text(dsn) if dsn else "",
            }
        return self._safe(run)
