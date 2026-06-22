"""P2 v21.3 - Tool Dependency Resolver."""

class ToolDependencyResolver:
    def resolve(self, dependencies: dict[str, list[str]], tool_name: str):
        return dependencies.get(tool_name, [])
