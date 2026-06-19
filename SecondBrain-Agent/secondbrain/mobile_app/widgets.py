from .models import MobileWidget
from .store import JsonStore


DEFAULT_WIDGETS = [
    MobileWidget("today", "Today", "summary").to_dict(),
    MobileWidget("capture", "Quick Capture", "action").to_dict(),
    MobileWidget("approvals", "Approvals", "inbox").to_dict(),
    MobileWidget("tasks", "Tasks", "list").to_dict(),
    MobileWidget("voice", "Voice Capture", "action").to_dict(),
]


class MobileWidgetRegistry:
    def __init__(self, store: JsonStore):
        self.store = store

    def widgets(self) -> list[dict]:
        existing = self.store.load("widgets", None)
        if existing is None:
            self.store.save("widgets", DEFAULT_WIDGETS)
            return DEFAULT_WIDGETS
        return existing

    def set_enabled(self, widget_id: str, enabled: bool) -> dict:
        widgets = self.widgets()
        updated = []
        result = None
        for widget in widgets:
            if widget["id"] == widget_id:
                widget = {**widget, "enabled": enabled}
                result = widget
            updated.append(widget)
        self.store.save("widgets", updated)
        return result or {"error": "widget_not_found", "widget_id": widget_id}
