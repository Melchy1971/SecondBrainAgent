"""P7 v25.0 - Mobile Dashboard."""

class MobileDashboard:
    def render(self, widgets: list[str]):
        return {
            "widgets": widgets,
            "count": len(widgets),
        }
