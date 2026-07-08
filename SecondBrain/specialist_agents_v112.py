from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import time

from .workflow_engine_v112 import WorkflowDefinition, step


@dataclass
class SpecialistAgentResult:
    agent: str
    objective: str
    workflow_id: str
    assumptions: list[str]
    risks: list[str]
    created_at: float


class BaseSpecialistAgent:
    name = "base"

    def build_workflow(self, objective: str, **kwargs: Any) -> WorkflowDefinition:
        raise NotImplementedError

    def describe(self, objective: str, workflow: WorkflowDefinition, assumptions: list[str], risks: list[str]) -> dict[str, Any]:
        return asdict(SpecialistAgentResult(self.name, objective, workflow.workflow_id, assumptions, risks, time.time()))


class EmailAgent(BaseSpecialistAgent):
    name = "email_agent"

    def build_workflow(self, objective: str, **kwargs: Any) -> WorkflowDefinition:
        query = kwargs.get("query") or objective
        s1 = step("sync_connectors", "connectors.sync")
        s2 = step("search_mail_context", "rag.search", {"query": f"Email Kontext: {query}", "limit": 8}, [s1.step_id])
        s3 = step("draft_email_brief", "rag.answer", {"query": f"Erstelle eine E-Mail-Arbeitszusammenfassung: {objective}", "limit": 5}, [s2.step_id])
        s4 = step("save_email_brief", "desktop.quick_capture", {"title": "Email Agent Brief", "text": f"Email Agent Ziel: {objective}"}, [s3.step_id])
        return WorkflowDefinition("email.agent.v112", "Email Agent Workflow", "Synchronisiert Quellen und erstellt E-Mail-Arbeitskontext.", [s1, s2, s3, s4], {"agent": self.name})


class CalendarAgent(BaseSpecialistAgent):
    name = "calendar_agent"

    def build_workflow(self, objective: str, **kwargs: Any) -> WorkflowDefinition:
        s1 = step("sync_calendar_sources", "connectors.sync")
        s2 = step("search_calendar_context", "rag.search", {"query": f"Kalender Termine Planung: {objective}", "limit": 8}, [s1.step_id])
        s3 = step("calendar_plan", "ai.ask", {"task": "calendar_agent", "prompt": f"Plane auf Basis vorhandener Kalenderinformationen: {objective}"}, [s2.step_id])
        s4 = step("save_calendar_plan", "desktop.quick_capture", {"title": "Calendar Agent Plan", "text": f"Calendar Agent Ziel: {objective}"}, [s3.step_id])
        return WorkflowDefinition("calendar.agent.v112", "Calendar Agent Workflow", "Erstellt Termin- und Tagesplanung ohne automatische Kalendereinträge.", [s1, s2, s3, s4], {"agent": self.name})


class ResearchAgent(BaseSpecialistAgent):
    name = "research_agent"

    def build_workflow(self, objective: str, **kwargs: Any) -> WorkflowDefinition:
        s1 = step("search_knowledge", "rag.search", {"query": objective, "limit": int(kwargs.get("limit", 10))})
        s2 = step("synthesize_answer", "rag.answer", {"query": objective, "limit": 8}, [s1.step_id])
        s3 = step("critique", "ai.ask", {"task": "research_agent", "prompt": f"Prüfe diese Recherchefrage auf Lücken, Annahmen und nächste Belege: {objective}"}, [s2.step_id])
        s4 = step("save_research_note", "desktop.quick_capture", {"title": "Research Agent Ergebnis", "text": f"Research Ziel: {objective}"}, [s3.step_id])
        return WorkflowDefinition("research.agent.v112", "Research Agent Workflow", "Sucht, synthetisiert und prüft Wissensantworten.", [s1, s2, s3, s4], {"agent": self.name})


class DocumentationAgent(BaseSpecialistAgent):
    name = "documentation_agent"

    def build_workflow(self, objective: str, **kwargs: Any) -> WorkflowDefinition:
        target = kwargs.get("target") or "docs/DEVELOPMENT_STATUS_v11.2.md"
        s1 = step("collect_status", "rag.search", {"query": f"Entwicklungsstand Dokumentation {objective}", "limit": 12})
        s2 = step("write_documentation", "rag.answer", {"query": f"Aktualisiere die technische Dokumentation für: {objective}", "limit": 8}, [s1.step_id])
        s3 = step("save_documentation_note", "desktop.quick_capture", {"title": "Documentation Agent Update", "text": f"Dokumentationsziel: {objective}\nZieldatei: {target}"}, [s2.step_id])
        return WorkflowDefinition("documentation.agent.v112", "Documentation Agent Workflow", "Sammelt Status und erzeugt Dokumentationsupdate.", [s1, s2, s3], {"agent": self.name, "target": target})


def build_specialist_workflow(agent: str, objective: str, **kwargs: Any) -> WorkflowDefinition:
    agents: dict[str, BaseSpecialistAgent] = {
        "email": EmailAgent(),
        "calendar": CalendarAgent(),
        "research": ResearchAgent(),
        "docs": DocumentationAgent(),
        "documentation": DocumentationAgent(),
    }
    key = agent.strip().lower()
    if key not in agents:
        raise KeyError(f"unknown_specialist_agent:{agent}")
    return agents[key].build_workflow(objective, **kwargs)
