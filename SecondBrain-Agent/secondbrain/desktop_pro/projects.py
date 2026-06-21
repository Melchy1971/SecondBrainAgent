class ProjectCenter:
    def __init__(self, store):
        self.store = store

    def projects(self) -> list[dict]:
        return self.store.load("projects", [])

    def add_project(self, name: str, status: str = "active", risk: str = "medium") -> dict:
        project = {"id": f"proj_{len(self.projects())+1}", "name": name, "status": status, "risk": risk}
        return self.store.append("projects", project)

    def summary(self) -> dict:
        projects = self.projects()
        return {
            "projects": len(projects),
            "active": sum(1 for p in projects if p.get("status") == "active"),
            "high_risk": sum(1 for p in projects if p.get("risk") == "high"),
        }
