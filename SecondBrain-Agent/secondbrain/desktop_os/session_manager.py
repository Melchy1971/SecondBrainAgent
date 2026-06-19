
from __future__ import annotations
from .json_store import JsonStore
from .models import DesktopSession, new_id, to_dict
import time

class DesktopSessionManager:
    def __init__(self, store: JsonStore):
        self.store = store
        if not self.store.read('session.json', None):
            self.store.write('session.json', to_dict(DesktopSession(new_id('dsk_session'))))

    def current(self):
        return self.store.read('session.json', {})

    def update(self, **changes):
        row = self.current()
        row.update({k:v for k,v in changes.items() if v is not None})
        row['updated_at'] = time.time()
        return self.store.write('session.json', row)

    def status(self):
        row = self.current()
        return {'component': 'desktop_session_v125', 'session_id': row.get('session_id'), 'active_view': row.get('active_view'), 'healthy': bool(row.get('session_id'))}
