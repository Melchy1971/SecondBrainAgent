"""P5 v30.19 - Settings Center with P1 embedding/store settings."""

from __future__ import annotations

from typing import Any


class SettingsCenter:
    EMBEDDING_FIELDS = {
        "SECONDBRAIN_EMBEDDING_PROVIDER": {"default": "local", "allowed": ["local", "ollama", "openai"]},
        "SECONDBRAIN_EMBEDDING_MODEL": {"default": None, "allowed": None},
        "SECONDBRAIN_EMBEDDING_DIMENSIONS": {"default": None, "allowed": None},
        "SECONDBRAIN_OLLAMA_BASE_URL": {"default": "http://localhost:11434", "allowed": None},
        "SECONDBRAIN_OPENAI_API_KEY_ENV": {"default": "OPENAI_API_KEY", "allowed": None},
        "SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK": {"default": False, "allowed": [False, True]},
        "SECONDBRAIN_EMBEDDING_TIMEOUT_SECONDS": {"default": 10.0, "allowed": None},
        "DATABASE_URL": {"default": None, "allowed": None},
    }

    def __init__(self):
        self._settings: dict[str, Any] = {}

    def set(self, key: str, value: Any):
        if key in self.EMBEDDING_FIELDS:
            allowed = self.EMBEDDING_FIELDS[key]["allowed"]
            if allowed is not None and value not in allowed:
                raise ValueError(f"Unsupported value for {key}")
        self._settings[key] = value

    def get(self, key: str, default=None):
        return self._settings.get(key, default)

    def export(self):
        return dict(self._settings)

    def render_embedding_settings(self) -> dict[str, Any]:
        fields = []
        for key, meta in self.EMBEDDING_FIELDS.items():
            fields.append({
                "key": key,
                "value": self._settings.get(key, meta["default"]),
                "default": meta["default"],
                "allowed": meta["allowed"],
                "secret": key in {"DATABASE_URL"} or key.endswith("API_KEY") or key.endswith("API_KEY_ENV"),
            })
        return {
            "schema": "secondbrain.gui.settings.embedding.v1",
            "sections": ["embedding", "store", "security"],
            "fields": fields,
            "commands": ["p1-embedding-config", "p1-provider-health", "p3-pgvector-readiness"],
        }
