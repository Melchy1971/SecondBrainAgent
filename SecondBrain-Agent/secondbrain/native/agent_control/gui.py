"""v30.66 Native Agent Control - GUI panel.

Renders the eight agent areas as tabs inside the native AI Workspace shell. This
is NOT a second application: ``AgentControlPanel`` is a ``ttk.Frame`` meant to be
embedded, and ``run_gui`` is only a standalone dev/preview entry point. All data
comes from :class:`AgentControlService` (UI-free ``view_model``), so the panel
holds no logic of its own. Tkinter is imported lazily so the module imports in
headless/test environments.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .service import AREAS, AgentControlService


def build_tabs(service: AgentControlService) -> list[dict[str, Any]]:
    """UI-free description of the tabs the GUI renders (testable)."""
    vm = service.view_model()
    return [{"id": area["id"], "title": area["title"], "ok": area["ok"],
             "lines": _area_lines(area["id"], area["data"])}
            for area in vm["areas"]]


def _area_lines(area_id: str, data: dict[str, Any]) -> list[str]:
    if not data.get("ok"):
        return [f"nicht verfügbar: {data.get('error') or data.get('status')}"]
    if area_id == "plans":
        return [f"{p['id']}  [{p['status']}]  {p['steps_completed']}/{p['steps']}  {p['goal'][:40]}"
                for p in data.get("plans", [])] or ["keine Pläne"]
    if area_id == "workflows":
        return [f"{w['workflow_id']}  [{w['state']}]  {w['steps_completed']}/{w['steps']}"
                for w in data.get("workflows", [])] or ["keine Workflows"]
    if area_id == "background_agents":
        return [f"{a['id']}  [{a['state']}]  {a['agent_type']}"
                for a in data.get("agents", [])] or ["keine Background Agents"]
    if area_id == "approvals":
        return [f"{a['approval_id']}  {a.get('command','')}  [{a.get('risk_level','')}]"
                for a in data.get("approvals", [])] or ["keine offenen Approvals"]
    if area_id == "goals":
        return [f"{g['id']}  [{g['status']}]  {round(g['progress']*100)}%  {g['title'][:40]}"
                for g in data.get("goals", [])] or ["keine Goals"]
    if area_id == "audit":
        return [f"{name}: {info['count']} Einträge" for name, info in data.get("trails", {}).items()]
    if area_id == "logs":
        return [f"{r.get('ts','')}  {r.get('event','')}" for r in data.get("logs", [])] or ["keine Logs"]
    if area_id == "agents":
        return [f"Pläne: {data.get('plans_total',0)}",
                f"Workflows: {data.get('workflows_total',0)}",
                f"Background Agents: {data.get('background_agents_total',0)} "
                f"({data.get('background_agents_active',0)} aktiv)"]
    return [str(data)]


def build_panel(master, project_root: str | Path):
    import tkinter as tk
    from tkinter import ttk

    service = AgentControlService(project_root)
    frame = ttk.Frame(master, padding=4)
    notebook = ttk.Notebook(frame)
    notebook.pack(fill="both", expand=True)
    for tab in build_tabs(service):
        page = ttk.Frame(notebook)
        listbox = tk.Listbox(page)
        for line in tab["lines"]:
            listbox.insert("end", line)
        listbox.pack(fill="both", expand=True)
        notebook.add(page, text=tab["title"])
    return frame


class AgentControlPanel:
    """Thin embeddable wrapper so the AI Workspace shell can host the surface."""

    def __init__(self, master, project_root: str | Path):
        self.frame = build_panel(master, project_root)

    def widget(self):
        return self.frame


def run_gui(project_root: str | Path = ".") -> int:
    try:
        import tkinter as tk
    except Exception as exc:  # pragma: no cover - headless
        print(f"tkinter_unavailable: {exc}")
        return 1
    root = tk.Tk()
    root.title("Agent Control Center")
    panel = AgentControlPanel(root, project_root)
    panel.widget().pack(fill="both", expand=True)
    root.mainloop()
    return 0
