"""P5 v23.1 - Widget Framework."""

class Widget:
    def __init__(self, widget_id: str, title: str):
        self.widget_id = widget_id
        self.title = title


class WidgetFramework:
    def __init__(self):
        self._widgets = {}

    def register(self, widget: Widget):
        self._widgets[widget.widget_id] = widget

    def list(self):
        return list(self._widgets.keys())
