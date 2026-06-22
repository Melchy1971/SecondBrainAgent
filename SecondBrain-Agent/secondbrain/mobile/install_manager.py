"""P7 v25.1 - Install and Update Manager."""

class InstallManager:
    def check_update(self, current: str, latest: str):
        return {
            "update_available": current != latest,
            "current": current,
            "latest": latest,
        }
