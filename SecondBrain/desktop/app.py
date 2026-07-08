from __future__ import annotations

from pathlib import Path

from .commands import Command, CommandPalette
from .events import EventBus
from .navigation import NavigationModel
from .notifications import NotificationCenter, NotificationLevel
from .router import DesktopRouter
from .shell import DesktopShell
from .state import DesktopStateStore
from .status_service import StatusColor, StatusService
from .view_registry import DesktopView, ViewRegistry
from .workspace_manager import WorkspaceManager
from secondbrain.gui.p1_control_panel import P1ControlPanel
from secondbrain.gui.production_dashboard import ProductionDashboard
from secondbrain.gui.rag_explorer import RagExplorer
from secondbrain.gui.settings_center import SettingsCenter


class DesktopApp:
    DEFAULT_VIEWS = [
        ("dashboard", "Dashboard", "home", 10),
        ("documents", "Documents", "file", 20),
        ("search", "Search", "search", 30),
        ("rag", "RAG", "brain", 40),
        ("rag-import", "RAG Import", "inbox", 41),
        ("rag-index", "Vector Index", "vector", 42),
        ("p1-control", "P1 Control", "shield", 43),
        ("production", "Production Gate", "gate", 44),
        ("connectors", "Connectors", "plug", 50),
        ("settings", "Settings", "gear", 90),
        ("settings-p1", "P1 Settings", "sliders", 91),
    ]

    def __init__(self, state_path: str | Path) -> None:
        self.state_store = DesktopStateStore(state_path)
        self.state = self.state_store.load()
        self.events = EventBus()
        self.router = DesktopRouter()
        self.views = ViewRegistry()
        self.navigation = NavigationModel(self.views)
        self.commands = CommandPalette()
        self.notifications = NotificationCenter()
        self.status = StatusService()
        self.workspaces = WorkspaceManager()
        self.p1_control = P1ControlPanel()
        self.rag_explorer = RagExplorer()
        self.production_dashboard = ProductionDashboard()
        self.settings_center = SettingsCenter()
        self.shell = DesktopShell(
            state=self.state,
            router=self.router,
            commands=self.commands,
            notifications=self.notifications,
            status=self.status,
            views=self.views,
            navigation=self.navigation,
        )
        self._started = False
        self._register_default_views()
        self._register_default_commands()
        self._register_default_statuses()

    def start(self) -> DesktopShell:
        self._started = True
        self.notifications.push("Desktop started", "Desktop shell is ready", NotificationLevel.SUCCESS)
        return self.shell

    def stop(self) -> None:
        self.save_state()
        self._started = False

    @property
    def is_started(self) -> bool:
        return self._started

    def _register_default_views(self) -> None:
        factories = {
            "dashboard": self._render_dashboard_view,
            "rag": self._render_rag_view,
            "rag-import": self.rag_explorer.render_import_center,
            "rag-index": self.rag_explorer.render_index_center,
            "p1-control": self.p1_control.render,
            "production": self.production_dashboard.render_p1,
            "settings": lambda: {"view": "settings"},
            "settings-p1": self.settings_center.render_embedding_settings,
        }
        for view_id, title, icon, order in self.DEFAULT_VIEWS:
            self.register_view(view_id, title, factories.get(view_id, lambda view_id=view_id: {"view": view_id}), icon=icon, order=order)

    def _render_dashboard_view(self) -> dict[str, object]:
        return {"view": "dashboard"}

    def _render_rag_view(self) -> dict[str, object]:
        return {
            "view": "rag",
            "panels": {
                "import": self.rag_explorer.render_import_center(),
                "index": self.rag_explorer.render_index_center(),
                "control": self.p1_control.render(),
            },
        }

    def register_view(self, view_id: str, title: str, factory, icon: str = "", order: int = 100, visible: bool = True) -> None:
        self.views.register(DesktopView(id=view_id, title=title, factory=factory, icon=icon, order=order, visible=visible))
        self.router.register(view_id, title, lambda view_id=view_id: self.views.render(view_id))

    def _register_default_commands(self) -> None:
        self.commands.register(Command("open.dashboard", "Open Dashboard", lambda: self.shell.open_view("dashboard"), "Ctrl+D", "navigation"))
        self.commands.register(Command("open.documents", "Open Documents", lambda: self.shell.open_view("documents"), "Ctrl+O", "navigation"))
        self.commands.register(Command("open.search", "Open Search", lambda: self.shell.open_view("search"), "Ctrl+F", "navigation"))
        self.commands.register(Command("open.settings", "Open Settings", lambda: self.shell.open_view("settings"), "Ctrl+,", "navigation"))
        self.commands.register(Command("open.rag-import", "Open RAG Import", lambda: self.shell.open_view("rag-import"), None, "navigation"))
        self.commands.register(Command("open.rag-index", "Open Vector Index", lambda: self.shell.open_view("rag-index"), None, "navigation"))
        self.commands.register(Command("open.p1-control", "Open P1 Control", lambda: self.shell.open_view("p1-control"), None, "navigation"))
        self.commands.register(Command("open.production", "Open Production Gate", lambda: self.shell.open_view("production"), None, "navigation"))
        self.commands.register(Command("open.settings-p1", "Open P1 Settings", lambda: self.shell.open_view("settings-p1"), None, "navigation"))
        for action in self.p1_control.actions():
            self.commands.register(Command(f"action.{action['id']}", action["title"], lambda action=action: action, None, "p1"))
        self.commands.register(Command("workspace.create", "Create Workspace", lambda: self.workspaces.create("Default"), None, "workspace"))

    def _register_default_statuses(self) -> None:
        for name in ["Database", "RAG", "Embeddings", "Connectors", "OCR", "Background Jobs"]:
            self.status.set_status(name, StatusColor.YELLOW, "not checked")

    def save_state(self) -> None:
        self.state_store.save(self.state)
