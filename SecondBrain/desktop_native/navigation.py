from __future__ import annotations

from dataclasses import dataclass


NAVIGATION_VIEWS: tuple[tuple[str, str, str], ...] = (
    ("dashboard", "Dashboard", "Dashboard"),
    ("assistant", "Assistant", "Assistent"),
    ("tasks", "Tasks", "Aufgaben"),
    ("projects", "Projects", "Projekte"),
    ("documents", "Documents", "Dokumente"),
    ("search", "Search", "Suche"),
    ("memory", "Memory", "Memory"),
    ("knowledge_graph", "Knowledge Graph", "Wissensgraph"),
    ("calendar", "Calendar", "Kalender"),
    ("mail", "Mail", "Mail"),
    ("briefings", "Briefings", "Briefings"),
    ("jobs", "Jobs", "Jobs"),
    ("connectors", "Connectors", "Konnektoren"),
    ("agents", "Agents", "Agenten"),
    ("approvals", "Approvals", "Freigaben"),
    ("backups", "Backups", "Backups"),
    ("settings", "Settings", "Einstellungen"),
    ("diagnostics", "Diagnostics", "Diagnose"),
)

VIEWS = tuple(display for _view_id, display, _spoken in NAVIGATION_VIEWS)
VIEW_BY_ID = {view_id: display for view_id, display, _spoken in NAVIGATION_VIEWS}


@dataclass(frozen=True)
class MenuEndpoint:
    kind: str
    target: str


MENU_ENDPOINTS: dict[str, MenuEndpoint] = {
    "Dashboard": MenuEndpoint("native", "dashboard"),
    "Assistant": MenuEndpoint("workspace", "chat"),
    "Tasks": MenuEndpoint("native", "tasks"),
    "Projects": MenuEndpoint("workspace", "projects"),
    "Documents": MenuEndpoint("workspace", "documents"),
    "Search": MenuEndpoint("live_data", "search"),
    "Memory": MenuEndpoint("workspace", "memory"),
    "Knowledge Graph": MenuEndpoint("workspace", "semantic"),
    "Calendar": MenuEndpoint("external", "calendar"),
    "Mail": MenuEndpoint("external", "mail"),
    "Briefings": MenuEndpoint("native", "briefings"),
    "Jobs": MenuEndpoint("native", "jobs"),
    "Connectors": MenuEndpoint("live_data", "connectors"),
    "Agents": MenuEndpoint("workspace", "agents"),
    "Approvals": MenuEndpoint("native", "approvals"),
    "Backups": MenuEndpoint("native", "backups"),
    "Settings": MenuEndpoint("launcher", "gui-bootstrap"),
    "Diagnostics": MenuEndpoint("native", "diagnostics"),
    "Imports": MenuEndpoint("workspace", "imports"),
    "Production": MenuEndpoint("launcher", "p1-production"),
    "Developer": MenuEndpoint("launcher", "command-index"),
}


def display_view(view_id: str) -> str:
    return VIEW_BY_ID.get(view_id, view_id.replace("_", " ").title())


def endpoint_for_view(view: str) -> MenuEndpoint:
    try:
        return MENU_ENDPOINTS[view]
    except KeyError as exc:
        raise ValueError(f"unknown desktop view: {view}") from exc
