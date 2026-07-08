"""P5 v23.1 - System Monitor."""

class SystemMonitor:
    def render(self, cpu: float, memory: float, active_jobs: int):
        return {
            "cpu": cpu,
            "memory": memory,
            "active_jobs": active_jobs,
            "status": "PASS",
        }
