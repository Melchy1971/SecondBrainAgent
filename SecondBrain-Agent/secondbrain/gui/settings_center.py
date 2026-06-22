"""P5 v23.1 - Settings Center."""

class SettingsCenter:
    def __init__(self):
        self._settings = {}

    def set(self, key: str, value):
        self._settings[key] = value

    def get(self, key: str, default=None):
        return self._settings.get(key, default)

    def export(self):
        return dict(self._settings)
