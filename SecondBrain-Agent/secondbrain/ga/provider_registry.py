"""v28.0 - Provider Registry."""

class ProviderRegistry:
    def __init__(self):
        self._providers = {}

    def register(self, name: str, provider: dict):
        self._providers[name] = provider

    def get(self, name: str):
        return self._providers.get(name)

    def list(self):
        return sorted(self._providers.keys())
