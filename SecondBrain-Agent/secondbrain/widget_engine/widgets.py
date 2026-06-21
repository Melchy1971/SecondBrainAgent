DEFAULT_WIDGETS = [
    {"id": "today", "name": "Today", "enabled": True},
    {"id": "tasks", "name": "Tasks", "enabled": True},
    {"id": "projects", "name": "Projects", "enabled": True},
    {"id": "calendar", "name": "Calendar", "enabled": True},
    {"id": "approvals", "name": "Approvals", "enabled": True},
    {"id": "recommendations", "name": "Recommendations", "enabled": True},
    {"id": "quick_capture", "name": "Quick Capture", "enabled": True},
]


class WidgetEngine:
    def __init__(self, store):
        self.store = store

    def widgets(self) -> list[dict]:
        widgets = self.store.load("widgets", None)
        if widgets is None:
            self.store.save("widgets", DEFAULT_WIDGETS)
            return DEFAULT_WIDGETS
        return widgets

    def set_enabled(self, widget_id: str, enabled: bool) -> dict:
        widgets = []
        changed = None
        for widget in self.widgets():
            if widget["id"] == widget_id:
                widget = {**widget, "enabled": enabled}
                changed = widget
            widgets.append(widget)
        self.store.save("widgets", widgets)
        return changed or {"ok": False, "error": "widget_not_found"}
