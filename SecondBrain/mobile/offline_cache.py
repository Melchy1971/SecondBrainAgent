"""P7 v25.0 - Offline Cache."""

class OfflineCache:
    def __init__(self):
        self._cache = {}

    def put(self, key: str, value):
        self._cache[key] = value

    def get(self, key: str):
        return self._cache.get(key)
