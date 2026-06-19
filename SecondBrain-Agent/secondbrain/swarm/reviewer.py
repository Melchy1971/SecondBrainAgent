
from __future__ import annotations
from typing import Any

class ReviewerAgent:
    name = "reviewer"

    def review(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        execution = context.get("execution", {})
        findings = context.get("research", {}).get("findings", [])
        score = 0.75
        if execution.get("status") == "completed":
            score += 0.1
        if findings:
            score += 0.05
        score = min(1.0, score)
        return {
            "agent": self.name,
            "quality_score": round(score, 2),
            "passed": score >= 0.75,
            "issues": [] if score >= 0.75 else ["low_confidence"],
        }
