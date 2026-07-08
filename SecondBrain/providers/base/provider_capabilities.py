"""v30.0 provider capability model."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderCapabilities:
    chat: bool
    embeddings: bool
    streaming: bool
    local: bool = False
    supports_system_prompt: bool = True
    supports_json_mode: bool = False
