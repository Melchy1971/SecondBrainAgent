"""v30.0 provider factory."""
from __future__ import annotations

from secondbrain.providers.anthropic.chat_provider import AnthropicProvider
from secondbrain.providers.gemini.chat_provider import GeminiProvider
from secondbrain.providers.ollama.chat_provider import OllamaProvider
from secondbrain.providers.openai.chat_provider import OpenAIProvider
from secondbrain.providers.routing.provider_manager import ProviderManager


def build_default_provider_manager() -> ProviderManager:
    manager = ProviderManager()
    manager.register(OpenAIProvider())
    manager.register(AnthropicProvider())
    manager.register(GeminiProvider())
    manager.register(OllamaProvider())
    return manager
