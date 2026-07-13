"""P5 v23.0 - Agent Runs Dashboard."""

class AgentRunsDashboard:
    def render(self, runs: list[dict], tools: list[dict] | None = None):
        tools = tools or []
        by_category: dict[str, int] = {}
        risk_summary: dict[str, int] = {}
        for tool in tools:
            category = str(tool.get("category") or "system")
            by_category[category] = by_category.get(category, 0) + 1
            risk = str(tool.get("risk_level") or "low")
            risk_summary[risk] = risk_summary.get(risk, 0) + 1

        used_tools: list[dict] = []
        for run in runs:
            plan = run.get("plan") if isinstance(run, dict) else None
            if isinstance(plan, dict):
                for tool in plan.get("metadata", {}).get("used_tools", []):
                    if isinstance(tool, dict):
                        used_tools.append(tool)

        return {
            "runs": len(runs),
            "items": runs,
            "tool_overview": {
                "count": len(tools),
                "by_category": by_category,
                "by_risk_level": risk_summary,
                "tools": tools,
            },
            "used_tools": used_tools,
        }
