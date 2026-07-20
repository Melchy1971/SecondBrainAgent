from __future__ import annotations


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


def display_view(view_id: str) -> str:
    return VIEW_BY_ID.get(view_id, view_id.replace("_", " ").title())
