"""P7 v25.1 - Mobile Synchronisation Manager."""

class MobileSyncManager:
    def __init__(self):
        self._jobs = []

    def schedule(self, target: str):
        self._jobs.append(target)

    def jobs(self):
        return list(self._jobs)
