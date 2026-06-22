"""P2 v21.0 - Tool Registry."""

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, callable] = {}

    def register(self, name: str, tool):
        self._tools[name] = tool

    def get(self, name: str):
        return self._tools.get(name)

    def list(self):
        return sorted(self._tools.keys())
