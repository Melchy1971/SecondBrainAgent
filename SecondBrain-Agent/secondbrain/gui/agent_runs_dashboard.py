"""P5 v23.0 - Agent Runs Dashboard."""

class AgentRunsDashboard:
    def render(self, runs: list[dict]):
        return {
            "runs": len(runs),
            "items": runs,
        }
