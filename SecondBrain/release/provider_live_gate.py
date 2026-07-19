"""Opt-in live certification for configured AI providers."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Mapping

PASS, CONDITIONAL_PASS, BLOCKED = "PASS", "CONDITIONAL_PASS", "BLOCKED"
REPORT_PATH = Path("runtime/reports/provider_live_gate.json")
SUPPORTED_PROVIDERS = {"openai", "ollama"}
VALID_READINESS = {"ready", "degraded", "blocked", "unavailable", "not_configured"}


class TimeoutTransport:
    def __init__(self, timeout: float) -> None:
        from secondbrain.providers.base.http_transport import JsonHttpTransport
        self.transport, self.timeout = JsonHttpTransport(), timeout

    def post_json(self, url, payload, headers=None, timeout=60.0):
        return self.transport.post_json(url, payload, headers, timeout=self.timeout)


def _safe_error(exc: BaseException) -> dict[str, Any]:
    return {"error_code": getattr(exc, "status_code", None) or type(exc).__name__,
            "retryable": bool(getattr(exc, "retryable", False)), "message": "provider request failed"}


def _validated_probe_result(expected_name: str, result: Mapping[str, Any]) -> dict[str, Any]:
    validated = dict(result)
    if validated.get("name") != expected_name or validated.get("readiness") not in VALID_READINESS:
        return {"name": expected_name, "readiness": "blocked", "model": "", "capabilities": {},
                "timeout_seconds": None, "latency_ms": None, "usage": {}, "estimated_cost": 0.0,
                "error_code": "invalid_probe_result", "retryable": False, "source": "unknown"}
    return validated


def _configs(env: Mapping[str, str]) -> list[dict[str, Any]]:
    timeout = max(1.0, min(float(env.get("PROVIDER_LIVE_TIMEOUT_SECONDS") or 20), 120.0))
    return [
        {"name": "openai", "configured": bool(env.get("OPENAI_API_KEY") and env.get("OPENAI_LIVE_MODEL")),
         "model": str(env.get("OPENAI_LIVE_MODEL") or ""), "embedding_model": str(env.get("OPENAI_EMBEDDING_MODEL") or "text-embedding-3-small"),
         "timeout": timeout, "source": "cloud"},
        {"name": "ollama", "configured": bool(env.get("OLLAMA_LIVE_MODEL")),
         "model": str(env.get("OLLAMA_LIVE_MODEL") or ""), "embedding_model": str(env.get("OLLAMA_EMBEDDING_MODEL") or env.get("OLLAMA_LIVE_MODEL") or ""),
         "timeout": timeout, "source": "local"},
    ]


def _provider(config: Mapping[str, Any], env: Mapping[str, str]):
    transport = TimeoutTransport(float(config["timeout"]))
    if config["name"] == "openai":
        from secondbrain.providers.openai.chat_provider import OpenAIProvider
        return OpenAIProvider(api_key=str(env.get("OPENAI_API_KEY") or ""),
                              base_url=str(env.get("OPENAI_BASE_URL") or "https://api.openai.com/v1"), transport=transport)
    from secondbrain.providers.ollama.chat_provider import OllamaProvider
    return OllamaProvider(base_url=str(env.get("OLLAMA_BASE_URL") or "http://localhost:11434"), transport=transport)


def _cost(config: Mapping[str, Any], usage: Mapping[str, Any], env: Mapping[str, str]) -> float:
    if config["name"] != "openai":
        return 0.0
    inputs = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
    outputs = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    return round((inputs * float(env.get("OPENAI_INPUT_PER_1M") or 0) +
                  outputs * float(env.get("OPENAI_OUTPUT_PER_1M") or 0)) / 1_000_000, 6)


def probe_provider(config: Mapping[str, Any], env: Mapping[str, str]) -> dict[str, Any]:
    from secondbrain.providers.base.provider_models import ChatMessage, CompletionRequest, EmbeddingRequest
    started = perf_counter()
    provider = _provider(config, env)
    response = provider.complete(CompletionRequest(model=str(config["model"]), max_tokens=24, temperature=0,
        messages=[ChatMessage("user", 'Return only this JSON object: {"live":true}')]))
    embedding = provider.embed(EmbeddingRequest(model=str(config["embedding_model"]), texts=["public synthetic provider gate text"]))
    try:
        structured = json.loads(response.content).get("live") is True
    except (json.JSONDecodeError, AttributeError):
        structured = False
    dimensions = len(embedding.vectors[0]) if embedding.vectors else 0
    return {"name": config["name"], "readiness": "ready" if structured and dimensions else "degraded",
            "model": config["model"], "embedding_model": config["embedding_model"],
            "capabilities": asdict(provider.capabilities), "timeout_seconds": config["timeout"],
            "latency_ms": round((perf_counter() - started) * 1000, 2),
            "usage": {k: int(v) for k, v in response.usage.items() if isinstance(v, int)},
            "estimated_cost": _cost(config, response.usage, env), "error_code": None, "retryable": False,
            "source": config["source"], "checks": {"chat": bool(response.content), "structured_json": structured,
            "embedding": dimensions > 0, "embedding_dimensions": dimensions}}


def run_provider_live_gate(project_root: str | Path = ".", *, env: Mapping[str, str] | None = None,
                           probe: Callable[[Mapping[str, Any], Mapping[str, str]], dict[str, Any]] = probe_provider,
                           write_report: bool = True) -> dict[str, Any]:
    source = os.environ if env is None else env
    required = {x.strip().lower() for x in str(source.get("REQUIRED_LIVE_PROVIDERS") or "").split(",") if x.strip()}
    unknown_required = sorted(required - SUPPORTED_PROVIDERS)
    configuration_error = None
    try:
        configs = _configs(source)
        max_cost = max(0.0, float(source.get("PROVIDER_LIVE_MAX_COST") or 0.05))
    except (ValueError, OverflowError):
        configs, max_cost = [], 0.0
        configuration_error = "invalid_numeric_setting"
    providers: list[dict[str, Any]] = []
    for config in configs:
        if not config["configured"]:
            providers.append({"name": config["name"], "readiness": "blocked" if config["name"] in required else "not_configured",
                "model": config["model"], "capabilities": {}, "timeout_seconds": config["timeout"], "latency_ms": None,
                "usage": {}, "estimated_cost": 0.0, "error_code": "not_configured", "retryable": False, "source": config["source"]})
            continue
        if config["source"] == "cloud" and str(source.get("PRIVACY_MODE") or "").lower() == "strict":
            providers.append({"name": config["name"], "readiness": "blocked", "model": config["model"],
                "capabilities": {}, "timeout_seconds": config["timeout"], "latency_ms": None, "usage": {},
                "estimated_cost": 0.0, "error_code": "privacy_mode_strict", "retryable": False, "source": "cloud"})
            continue
        try:
            result = _validated_probe_result(config["name"], probe(config, source))
            if float(result.get("estimated_cost") or 0) > max_cost:
                result.update(readiness="blocked", error_code="cost_limit_exceeded")
            providers.append(result)
        except Exception as exc:
            providers.append({"name": config["name"], "readiness": "unavailable", "model": config["model"],
                "capabilities": {}, "timeout_seconds": config["timeout"], "latency_ms": None, "usage": {},
                "estimated_cost": 0.0, "source": config["source"], **_safe_error(exc)})
    critical = [p["name"] for p in providers if p["readiness"] in {"blocked", "unavailable"}]
    critical.extend(unknown_required)
    if configuration_error:
        critical.append("configuration")
    degraded = [p["name"] for p in providers if p["readiness"] in {"degraded", "not_configured"}]
    status = BLOCKED if critical else (CONDITIONAL_PASS if degraded else PASS)
    report = {"schema": "secondbrain.provider_live_gate.v1", "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status, "ok": status != BLOCKED, "providers": providers, "required_providers": sorted(required),
        "failed_providers": critical, "privacy": {"cloud_requires_explicit_configuration": True, "test_content": "synthetic_public_only"},
        "fallback": {"automatic": False, "policy": "explicit_provider_per_probe"}, "limits": {"max_cost": max_cost}}
    if configuration_error:
        report["configuration_error"] = configuration_error
    if write_report:
        target = Path(project_root).resolve() / REPORT_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report["report"] = REPORT_PATH.as_posix()
    return report
