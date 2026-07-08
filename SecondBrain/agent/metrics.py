"""P2 v21.3 - Agent Metrics."""

class AgentMetrics:
    def summarize(self, sessions: int, tasks: int, failures: int):
        success_rate = 0.0 if tasks == 0 else ((tasks - failures) / tasks)
        return {
            "sessions": sessions,
            "tasks": tasks,
            "failures": failures,
            "success_rate": round(success_rate, 3),
        }
