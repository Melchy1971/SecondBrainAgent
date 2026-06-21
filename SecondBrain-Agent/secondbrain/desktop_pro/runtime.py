from .store import DesktopStore
from .layout import DockLayoutManager
from .command_palette import CommandPalette
from .knowledge_explorer import KnowledgeExplorer
from .memory_explorer import MemoryExplorer
from .kanban import KanbanBoard
from .projects import ProjectCenter


class DesktopOSPro:
    def __init__(self, root="."):
        self.store = DesktopStore(root)
        self.layout = DockLayoutManager(self.store)
        self.commands = CommandPalette(self.store)
        self.knowledge = KnowledgeExplorer(self.store)
        self.memory = MemoryExplorer(self.store)
        self.kanban = KanbanBoard(self.store)
        self.projects = ProjectCenter(self.store)

    def status(self) -> dict:
        layout = self.layout.layout()
        return {
            "version": "13.3",
            "windows": len(layout["windows"]),
            "visible_windows": sum(1 for w in layout["windows"] if w.get("visible")),
            "commands": len(self.commands.commands()),
            "knowledge_nodes": len(self.knowledge.nodes()),
            "memories": len(self.memory.memories()),
            "kanban_cards": len(self.kanban.cards()),
            "projects": self.projects.summary(),
            "gui_backend": "pyside6_ready",
        }
