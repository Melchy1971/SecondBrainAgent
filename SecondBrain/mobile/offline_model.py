"""P7 v25.1 - Offline First Data Model."""

class OfflineFirstModel:
    def merge(self, local: dict, remote: dict):
        result = dict(local)
        result.update(remote)
        return result
