"""P4 v22.1 - Conflict Resolution."""

class ConflictResolver:
    def resolve(self, local_version: dict, remote_version: dict):
        local_ts = local_version.get("updated_at", 0)
        remote_ts = remote_version.get("updated_at", 0)
        return remote_version if remote_ts >= local_ts else local_version
