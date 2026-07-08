DEFAULT_LAYOUT = {
    "theme": "dark",
    "windows": [
        {"id": "dashboard", "title": "Dashboard", "dock": "center", "visible": True},
        {"id": "knowledge", "title": "Knowledge Explorer", "dock": "left", "visible": True},
        {"id": "memory", "title": "Memory Explorer", "dock": "right", "visible": True},
        {"id": "kanban", "title": "Kanban", "dock": "bottom", "visible": False},
    ],
}


class DockLayoutManager:
    def __init__(self, store):
        self.store = store

    def layout(self) -> dict:
        layout = self.store.load("layout", None)
        if layout is None:
            self.store.save("layout", DEFAULT_LAYOUT)
            return DEFAULT_LAYOUT
        return layout

    def set_window_visible(self, window_id: str, visible: bool) -> dict:
        layout = self.layout()
        changed = None
        windows = []
        for w in layout["windows"]:
            if w["id"] == window_id:
                w = {**w, "visible": visible}
                changed = w
            windows.append(w)
        layout["windows"] = windows
        self.store.save("layout", layout)
        return changed or {"ok": False, "error": "window_not_found"}
