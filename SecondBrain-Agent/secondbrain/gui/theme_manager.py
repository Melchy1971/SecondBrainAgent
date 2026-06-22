"""P5 v23.1 - Theme and Layout System."""

class ThemeManager:
    THEMES = ["light", "dark", "system"]

    def __init__(self):
        self.theme = "system"

    def set_theme(self, theme: str):
        if theme not in self.THEMES:
            raise ValueError("Unsupported theme")
        self.theme = theme
