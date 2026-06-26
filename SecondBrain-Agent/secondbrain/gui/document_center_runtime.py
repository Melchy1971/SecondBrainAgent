"""v30.23 Document Center runtime truth service.

Read-only aggregation layer for the HUD/GUI. It connects the visible Documents
view to the actual P1 RAG index, parser metadata and import reports instead of
showing only raw Vault markdown files.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from secondbrain.document_understanding.parsers import MIME_BY_EXTENSION, default_parser_registry
from secondbrain.p1_rag_runtime import P1RagRuntime

SCHEMA = "secondbrain.gui.document_center.v1"
SUPPORTED_EXTENSIONS = tuple(sorted(MIME_BY_EXTENSION.keys()))


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except Exception:
        return default


def _safe_json(path: Path) -> dict[str, Any]:
    try:
        if path.exists() and path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}
    return {}


def _read_env(root: Path) -> dict[str, str]:
    env_path = root / ".env"
    values: dict[str, str] = {}
    try:
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        pass
    return values


@dataclass(frozen=True)
class DocumentCenterRuntime:
    project_root: str | Path
    profile: str | None = None

    @property
    def root(self) -> Path:
        return Path(self.project_root).resolve()

    @property
    def reports_dir(self) -> Path:
        return self.root / "runtime" / "reports"

    @property
    def import_dirs(self) -> list[Path]:
        return [
            self.root / "runtime" / "imports",
            self.root / "inbox",
            self.root / "SecondBrain" / "00_Inbox",
        ]

    def _rag(self) -> P1RagRuntime:
        return P1RagRuntime(self.root, self.profile)

    def _runtime_truth(self) -> dict[str, Any]:
        env = _read_env(self.root)
        database_url = env.get("DATABASE_URL", "")
        embedding_provider = env.get("SECONDBRAIN_EMBEDDING_PROVIDER", "local")
        embedding_model = env.get("SECONDBRAIN_EMBEDDING_MODEL", "")
        embedding_dim = env.get("SECONDBRAIN_EMBEDDING_DIMENSIONS", "")
        has_openai_key = bool(env.get("OPENAI_API_KEY") or env.get("SECONDBRAIN_OPENAI_API_KEY"))
        return {
            "database_configured": bool(database_url),
            "database_kind": "postgresql" if database_url.startswith("postgresql") else ("sqlite" if not database_url else "unknown"),
            "embedding_provider": embedding_provider,
            "embedding_model": embedding_model,
            "embedding_dimensions": _safe_int(embedding_dim, 0),
            "openai_key_configured": has_openai_key,
        }

    def _last_report(self, pattern: str) -> dict[str, Any]:
        try:
            matches = sorted(self.reports_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        except Exception:
            matches = []
        if not matches:
            return {"exists": False}
        path = matches[0]
        data = _safe_json(path)
        return {
            "exists": True,
            "path": str(path),
            "name": path.name,
            "mtime": int(path.stat().st_mtime),
            "ok": data.get("ok"),
            "status": data.get("status"),
            "schema": data.get("schema"),
            "data": data,
        }

    def _pending_imports(self) -> dict[str, Any]:
        files: list[dict[str, Any]] = []
        counts = Counter()
        for folder in self.import_dirs:
            if not folder.exists() or not folder.is_dir():
                continue
            for path in folder.rglob("*"):
                if not path.is_file() or path.name.startswith("."):
                    continue
                suffix = path.suffix.lower()
                if suffix not in SUPPORTED_EXTENSIONS and suffix != ".zip":
                    continue
                try:
                    st = path.stat()
                except Exception:
                    continue
                status = "supported" if suffix in SUPPORTED_EXTENSIONS else "zip_upload"
                counts[status] += 1
                files.append({
                    "name": path.name,
                    "path": str(path),
                    "extension": suffix or "",
                    "mime_type": MIME_BY_EXTENSION.get(suffix, "application/zip" if suffix == ".zip" else "unknown"),
                    "size": st.st_size,
                    "mtime": int(st.st_mtime),
                    "status": status,
                })
        files.sort(key=lambda item: item["mtime"], reverse=True)
        return {"total": len(files), "counts": dict(counts), "files": files[:100]}

    def status(self) -> dict[str, Any]:
        try:
            rag = self._rag()
            rag_status = rag.status()
            sources = rag.sources()
            validation = rag.validate_index(write_report=False)
            embedding = rag.embedding_status()
        except Exception as exc:  # noqa: BLE001 - GUI status must degrade, not crash
            truth = self._runtime_truth()
            pending = self._pending_imports()
            return {
                "schema": SCHEMA,
                "ok": False,
                "status": "blocked",
                "generated_at": _utc_now(),
                "error": "document_center_runtime_failed",
                "detail": str(exc),
                "summary": {
                    "indexed_documents": 0,
                    "chunks": 0,
                    "tokens": 0,
                    "vectors": 0,
                    "pending_imports": pending.get("total", 0),
                    "ocr_required": 0,
                    "parse_errors": 0,
                    "validation_blockers": 1,
                    "validation_warnings": 0,
                },
                "runtime_truth": truth,
                "store": {"ok": False, "error": str(exc)},
                "embedding": {"ok": False, "error": str(exc)},
                "validation": {"ok": False, "status": "blocked", "blockers": 1, "warnings": 0, "findings": [{"severity": "blocker", "code": "runtime_failed", "detail": str(exc)}]},
                "parsers": {"supported_extensions": list(SUPPORTED_EXTENSIONS), "registered": sorted(getattr(default_parser_registry(), "_parsers", {}).keys()), "by_parser": {}, "by_mime_type": {}},
                "indexed_files": [],
                "pending_imports": pending,
                "reports": {},
            }
        source_items = list(sources.get("sources", [])) if sources.get("ok") else []
        parser_counts: Counter[str] = Counter()
        mime_counts: Counter[str] = Counter()
        ocr_required = 0
        parse_errors = 0
        indexed_files: list[dict[str, Any]] = []
        for item in source_items:
            metadata = dict(item.get("metadata") or {})
            parser = str(metadata.get("parser") or metadata.get("parser_detail") or "unknown")
            mime_type = str(metadata.get("mime_type") or metadata.get("parser_mime_type") or metadata.get("mime") or "unknown")
            parser_counts[parser] += 1
            mime_counts[mime_type] += 1
            if metadata.get("ocr_required"):
                ocr_required += 1
            if metadata.get("parse_errors"):
                parse_errors += 1
            indexed_files.append({
                "document_id": item.get("document_id"),
                "title": item.get("title"),
                "source": item.get("source"),
                "chunks": _safe_int(item.get("chunks")),
                "tokens": _safe_int(item.get("tokens")),
                "mime_type": mime_type,
                "parser": parser,
                "ocr_required": bool(metadata.get("ocr_required")),
                "parse_errors": metadata.get("parse_errors") or [],
                "created_at": item.get("created_at"),
            })
        validation_findings = list(validation.get("findings", [])) if isinstance(validation.get("findings"), list) else []
        blockers = [f for f in validation_findings if f.get("severity") == "blocker"]
        warnings = [f for f in validation_findings if f.get("severity") == "warning"]
        pending = self._pending_imports()
        truth = self._runtime_truth()
        last_migration = self._last_report("*migration*.json")
        last_reindex = self._last_report("*reindex*.json")
        last_vector_audit = self._last_report("*vector*latest*.json")
        status = "pass"
        if blockers or not rag_status.get("ok") or not embedding.get("ok"):
            status = "blocked"
        elif warnings or pending.get("total", 0) or ocr_required or parse_errors:
            status = "warning"
        return {
            "schema": SCHEMA,
            "ok": status != "blocked",
            "status": status,
            "generated_at": _utc_now(),
            "summary": {
                "indexed_documents": _safe_int(rag_status.get("documents")),
                "chunks": _safe_int(rag_status.get("chunks")),
                "tokens": _safe_int(rag_status.get("tokens")),
                "vectors": _safe_int((rag_status.get("store") or {}).get("vectors")),
                "pending_imports": pending.get("total", 0),
                "ocr_required": ocr_required,
                "parse_errors": parse_errors,
                "validation_blockers": len(blockers),
                "validation_warnings": len(warnings),
            },
            "runtime_truth": truth,
            "store": rag_status.get("store", {}),
            "embedding": embedding,
            "validation": {
                "ok": validation.get("ok"),
                "status": validation.get("status"),
                "blockers": len(blockers),
                "warnings": len(warnings),
                "findings": validation_findings[:30],
            },
            "parsers": {
                "supported_extensions": list(SUPPORTED_EXTENSIONS),
                "registered": sorted(getattr(default_parser_registry(), "_parsers", {}).keys()),
                "by_parser": dict(parser_counts),
                "by_mime_type": dict(mime_counts),
            },
            "indexed_files": indexed_files[:200],
            "pending_imports": pending,
            "reports": {
                "last_migration": last_migration,
                "last_reindex": last_reindex,
                "last_vector_audit": last_vector_audit,
            },
        }


def document_center_status(project_root: str | Path, profile: str | None = None) -> dict[str, Any]:
    return DocumentCenterRuntime(project_root, profile).status()
