from datetime import datetime, timezone
from uuid import uuid4


DEFAULT_JOBS = [
    {"name": "connector_sync", "interval": "hourly", "target": "connectors.sync_all"},
    {"name": "rag_index", "interval": "daily", "target": "rag.index"},
    {"name": "knowledge_compression", "interval": "daily", "target": "memory.compress"},
    {"name": "learning_reflection", "interval": "daily", "target": "learning.reflect"},
    {"name": "goal_forecast", "interval": "daily", "target": "goals.forecast"},
    {"name": "backup_verify", "interval": "weekly", "target": "ops.backup_verify"},
]


class BackgroundJobScheduler:
    def __init__(self, store):
        self.store = store

    def jobs(self) -> list[dict]:
        jobs = self.store.load("jobs", None)
        if jobs is None:
            self.store.save("jobs", DEFAULT_JOBS)
            jobs = DEFAULT_JOBS
        return jobs

    def run_due(self) -> list[dict]:
        runs = self.store.load("job_runs", [])
        created = []
        for job in self.jobs():
            run = {
                "id": str(uuid4()),
                "job": job["name"],
                "target": job["target"],
                "status": "simulated_success",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            runs.append(run)
            created.append(run)
        self.store.save("job_runs", runs)
        return created

    def runs(self, limit: int = 50) -> list[dict]:
        return self.store.load("job_runs", [])[-limit:]
