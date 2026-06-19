
from __future__ import annotations
from .json_store import JsonStore
from .models import WidgetDefinition, to_dict

DEFAULT_WIDGETS = [
    WidgetDefinition('system_health', 'System Health', 'metric', True, 10),
    WidgetDefinition('agent_activity', 'Agent Activity', 'feed', True, 20),
    WidgetDefinition('rag_search', 'Knowledge Search', 'search', True, 30),
    WidgetDefinition('swarm_tasks', 'Swarm Tasks', 'feed', True, 40),
    WidgetDefinition('notifications', 'Notifications', 'feed', True, 50),
    WidgetDefinition('quick_capture', 'Quick Capture', 'input', True, 60),
]

class WidgetRegistry:
    def __init__(self, store: JsonStore):
        self.store = store
        if not self.store.read('widgets.json', None):
            self.store.write('widgets.json', [to_dict(w) for w in DEFAULT_WIDGETS])

    def list(self, enabled: bool | None = None):
        rows = self.store.read('widgets.json', [])
        if enabled is not None:
            rows = [r for r in rows if bool(r.get('enabled')) is enabled]
        return sorted(rows, key=lambda r: (r.get('order', 100), r.get('widget_id', '')))

    def set_enabled(self, widget_id: str, enabled: bool):
        rows = self.store.read('widgets.json', [])
        found = False
        for row in rows:
            if row.get('widget_id') == widget_id:
                row['enabled'] = enabled
                found = True
        if not found:
            raise KeyError(f'Unknown widget: {widget_id}')
        return self.store.write('widgets.json', rows)

    def status(self):
        rows = self.list()
        return {'component': 'widget_registry_v125', 'widgets': len(rows), 'enabled': sum(1 for r in rows if r.get('enabled')), 'healthy': True}
