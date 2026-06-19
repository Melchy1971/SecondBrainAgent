
from __future__ import annotations
from typing import Any
import time

class DashboardBackend:
    def __init__(self, desktop_kernel: Any):
        self.desktop = desktop_kernel

    def snapshot(self):
        services = self.desktop.service_status_provider() if self.desktop.service_status_provider else {}
        return {
            'component': 'desktop_dashboard_v125',
            'version': '12.5',
            'generated_at': time.time(),
            'desktop': self.desktop.status(),
            'services': services,
            'widgets': self.desktop.widgets.list(enabled=True),
            'notifications': self.desktop.notifications.list(limit=10),
            'commands': self.desktop.commands.list(),
        }

    def activity_feed(self):
        rows = []
        for n in self.desktop.notifications.list(limit=25):
            rows.append({'type': 'notification', 'title': n.get('title'), 'level': n.get('level'), 'created_at': n.get('created_at')})
        return sorted(rows, key=lambda r: r.get('created_at', 0), reverse=True)
