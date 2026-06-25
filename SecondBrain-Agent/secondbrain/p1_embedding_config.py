from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

P1_EMBEDDING_CONFIG_SCHEMA = "secondbrain.p1_embedding_config.v1"
KNOWN_PROVIDERS = {"local", "local-deterministic", "deterministic", "ollama", "openai"}
PRODUCTION_PROVIDERS = {"ollama", "openai"}


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise ValueError(f"invalid_integer_env:{name}") from exc
    if value <= 0:
        raise ValueError(f"non_positive_integer_env:{name}")
    return value


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw.strip())
    except ValueError as exc:
        raise ValueError(f"invalid_float_env:{name}") from exc
    if value <= 0:
        raise ValueError(f"non_positive_float_env:{name}")
    return value


@dataclass(frozen=True)
class EmbeddingConfig:
    provider: str
    model: str | None
    dimensions: int
    ollama_base_url: str
    openai_api_key_env: str
    allow_fallback: bool
    timeout_seconds: float
    source: str
    dimensions_source: str = "explicit"

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "dimensions": self.dimensions,
            "ollama_base_url": self.ollama_base_url,
            "openai_api_key_env": self.openai_api_key_env,
            "allow_fallback": self.allow_fallback,
            "timeout_seconds": self.timeout_seconds,
            "source": self.source,
            "dimensions_source": self.dimensions_source,
        }


def _read_yaml_like_config(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip().lower()] = value.strip().strip('"\'')
    return result


def load_embedding_config(project_root: str | Path, profile: str | None = None) -> EmbeddingConfig:
    root = Path(project_root)
    config_path = root / "config" / "vector_rag.yaml"
    file_cfg = _read_yaml_like_config(config_path)
    source = "env"

    provider = os.getenv("SECONDBRAIN_EMBEDDING_PROVIDER", "").strip().lower()
    if not provider:
        provider = file_cfg.get("embedding_provider") or file_cfg.get("provider") or "local"
        source = "config" if file_cfg else "default"
    provider = provider.strip().lower()

    if provider not in KNOWN_PROVIDERS:
        raise ValueError(f"unknown_embedding_provider:{provider}")

    model = os.getenv("SECONDBRAIN_EMBEDDING_MODEL", "").strip() or file_cfg.get("embedding_model") or file_cfg.get("model") or None
    raw_dimensions = os.getenv("SECONDBRAIN_EMBEDDING_DIMENSIONS", "").strip() or file_cfg.get("embedding_dimensions") or file_cfg.get("dimensions")
    if raw_dimensions:
        dimensions = _env_int("SECONDBRAIN_EMBEDDING_DIMENSIONS", int(raw_dimensions)) if os.getenv("SECONDBRAIN_EMBEDDING_DIMENSIONS", "").strip() else int(raw_dimensions)
        if dimensions <= 0:
            raise ValueError("non_positive_embedding_dimensions")
        dimensions_source = "explicit"
    else:
        dimensions = 1536 if provider == "openai" else 768 if provider == "ollama" else 64
        dimensions_source = "provider_default"
    ollama_base_url = os.getenv("SECONDBRAIN_OLLAMA_BASE_URL", "").strip() or file_cfg.get("ollama_base_url") or "http://localhost:11434"
    openai_api_key_env = os.getenv("SECONDBRAIN_OPENAI_API_KEY_ENV", "").strip() or file_cfg.get("openai_api_key_env") or "OPENAI_API_KEY"
    allow_fallback = _env_flag("SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK", False)
    timeout_seconds = _env_float("SECONDBRAIN_EMBEDDING_TIMEOUT_SECONDS", float(file_cfg.get("embedding_timeout_seconds") or 10.0))

    return EmbeddingConfig(
        provider=provider,
        model=model,
        dimensions=dimensions,
        ollama_base_url=ollama_base_url,
        openai_api_key_env=openai_api_key_env,
        allow_fallback=allow_fallback,
        timeout_seconds=timeout_seconds,
        source=source,
        dimensions_source=dimensions_source,
    )


def evaluate_embedding_config(project_root: str | Path, *, production: bool = True, write_report: bool = False) -> dict[str, Any]:
    blockers: list[str] = []
    warnings: list[str] = []
    try:
        cfg = load_embedding_config(project_root)
        config_payload = cfg.to_dict()
    except Exception as exc:  # noqa: BLE001 - config boundary
        cfg = None
        config_payload = None
        blockers.append(str(exc))

    if cfg is not None:
        if production and cfg.provider not in PRODUCTION_PROVIDERS:
            blockers.append("embedding_provider_not_allowed_for_production")
        if cfg.allow_fallback:
            warnings.append("embedding_fallback_enabled")
            if production:
                blockers.append("embedding_fallback_must_be_disabled_for_production_gate")
        if cfg.provider == "openai" and not os.getenv(cfg.openai_api_key_env, "").strip():
            blockers.append("openai_api_key_env_not_set")
        if cfg.provider == "ollama" and not cfg.ollama_base_url.startswith(("http://", "https://")):
            blockers.append("ollama_base_url_invalid")
        if cfg.dimensions < 8:
            blockers.append("embedding_dimensions_too_small")
        if cfg.timeout_seconds <= 0:
            blockers.append("embedding_timeout_invalid")

    payload = {
        "schema": P1_EMBEDDING_CONFIG_SCHEMA,
        "ok": not blockers,
        "status": "pass" if not blockers else "blocked",
        "production": production,
        "blockers": blockers,
        "warnings": warnings,
        "config": config_payload,
        "remediation": None if not blockers else "set SECONDBRAIN_EMBEDDING_PROVIDER to ollama/openai, disable fallback for production, and configure provider credentials/endpoints",
    }
    if write_report:
        reports_dir = Path(project_root).resolve() / "runtime" / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        target = reports_dir / "p1_embedding_config_latest.json"
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        payload["report"] = {"path": str(target), "bytes": target.stat().st_size}
    return payload
