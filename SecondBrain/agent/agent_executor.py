"""P2 v21.0 - Agent Executor Foundation."""

class AgentExecutor:
    def __init__(self, tool_registry):
        self.tool_registry = tool_registry

    def execute(self, tool_name: str, *args, **kwargs):
        tool = self.tool_registry.get(tool_name)
        if tool is None:
            raise ValueError(f"Unknown tool: {tool_name}")
        return tool(*args, **kwargs)
