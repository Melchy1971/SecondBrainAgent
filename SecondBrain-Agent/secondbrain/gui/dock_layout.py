"""P5 v23.2 - Dockable Multi-Panel Layout."""

class DockLayout:
    def __init__(self):
        self._panels = {}

    def register(self, panel_id: str, position: str):
        self._panels[panel_id] = position

    def layout(self):
        return dict(self._panels)
