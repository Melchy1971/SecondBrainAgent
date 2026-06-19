
from __future__ import annotations
from .json_store import JsonStore
from .models import Notification, new_id, to_dict
import time

class NotificationCenter:
    def __init__(self, store: JsonStore):
        self.store = store

    def notify(self, title: str, body: str, level: str = 'info'):
        if level not in {'info', 'warning', 'error', 'success'}:
            raise ValueError('level must be info, warning, error or success')
        row = to_dict(Notification(new_id('ntf'), title.strip() or 'Notification', body.strip(), level))
        rows = self.store.read('notifications.json', [])
        rows.append(row)
        self.store.write('notifications.json', rows[-500:])
        return row

    def list(self, unread_only: bool = False, limit: int = 50):
        rows = self.store.read('notifications.json', [])
        if unread_only:
            rows = [r for r in rows if not r.get('read')]
        return sorted(rows, key=lambda r: r.get('created_at', 0), reverse=True)[:limit]

    def mark_read(self, notification_id: str):
        rows = self.store.read('notifications.json', [])
        found = False
        for row in rows:
            if row.get('notification_id') == notification_id:
                row['read'] = True
                found = True
        if not found:
            raise KeyError(f'Unknown notification: {notification_id}')
        self.store.write('notifications.json', rows)
        return {'notification_id': notification_id, 'read': True, 'updated_at': time.time()}

    def status(self):
        rows = self.store.read('notifications.json', [])
        return {'component': 'notification_center_v125', 'notifications': len(rows), 'unread': sum(1 for r in rows if not r.get('read')), 'healthy': True}
