from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import os

from .config import load_simple_yaml


class Provider(Protocol):
    name: str
    def generate(self, prompt: str, *, task: str = "default") -> str: ...


@dataclass
class EchoProvider:
    """Deterministic offline provider for tests, dry-runs and safe installation."""
    name: str = "echo"

    def generate(self, prompt: str, *, task: str = "default") -> str:
        return f"[echo:{task}] " + prompt[:1200]


@dataclass
class OllamaProvider:
    base_url: str = "http://localhost:11434"
    model: str = "llama3.1"
    name: str = "ollama"

    def generate(self, prompt: str, *, task: str = "default") -> str:
        from .ollama_client import ollama_generate
        return ollama_generate(self.base_url, self.model, prompt, timeout=120)


@dataclass
class RoutedTask:
    task: str
    prompt: str
    provider: str
    model: str | None = None
    max_context_chars: int = 12000
    require_validation: bool = True


class ModelRouter:
    def __init__(self, providers: dict[str, Provider], default_provider: str = "echo"):
        if default_provider not in providers:
            raise ValueError(f"default provider not configured: {default_provider}")
        self.providers = providers
        self.default_provider = default_provider

    def route(self, task: str, prompt: str, preferred_provider: str | None = None) -> RoutedTask:
        provider = preferred_provider or self.default_provider
        if provider not in self.providers:
            provider = self.default_provider
        clipped = prompt[:12000]
        return RoutedTask(task=task, prompt=clipped, provider=provider)

    def run(self, task: str, prompt: str, preferred_provider: str | None = None) -> str:
        routed = self.route(task, prompt, preferred_provider)
        answer = self.providers[routed.provider].generate(routed.prompt, task=routed.task)
        return validate_response(answer)


def validate_response(answer: str) -> str:
    if not answer or not answer.strip():
        raise ValueError("empty model response")
    if len(answer) > 50000:
        raise ValueError("model response too large")
    return answer.strip()


def load_model_router(project_root: Path) -> ModelRouter:
    cfg = load_simple_yaml(project_root / "config" / "ai_runtime_v105.yaml").get("ai_runtime", {})
    default_provider = cfg.get("default_provider", "echo")
    providers: dict[str, Provider] = {"echo": EchoProvider()}
    if cfg.get("ollama_enabled", False) or os.getenv("SECOND_BRAIN_OLLAMA_ENABLED") == "1":
        providers["ollama"] = OllamaProvider(base_url=cfg.get("ollama_base_url", "http://localhost:11434"), model=cfg.get("ollama_model", "llama3.1"))
    if default_provider not in providers:
        default_provider = "echo"
    return ModelRouter(providers, default_provider)


def build_context(records: list[dict], max_chars: int = 12000) -> str:
    parts: list[str] = []
    used = 0
    for record in records:
        title = str(record.get("title", "Unbenannt"))
        body = str(record.get("body", ""))
        block = f"## {title}\n{body}\n"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n".join(parts)
