"""P2 v21.0 - Workflow Engine Foundation."""

class WorkflowEngine:
    def run(self, graph):
        return {
            "status": "PASS",
            "tasks": len(graph.list()),
        }
