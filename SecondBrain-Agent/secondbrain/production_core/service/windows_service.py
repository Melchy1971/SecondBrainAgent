from datetime import datetime, timezone
from uuid import uuid4


class WindowsServiceManager:
    """
    Windows-service-ready abstraction.
    This does not install a real service by itself; it creates deterministic service metadata
    and scripts that can later be wired to pywin32/win32serviceutil.
    """
    def __init__(self, store):
        self.store = store

    def install_plan(self, service_name: str = "SecondBrainOS") -> dict:
        plan = {
            "service_name": service_name,
            "display_name": "SecondBrain OS Runtime",
            "start_type": "auto",
            "entrypoint": "python launcher.py prod-service-run",
            "status": "planned",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.save("windows_service_plan", plan)
        return plan

    def mark_installed(self, service_name: str = "SecondBrainOS") -> dict:
        state = {
            "id": str(uuid4()),
            "service_name": service_name,
            "status": "installed",
            "installed_at": datetime.now(timezone.utc).isoformat(),
        }
        self.store.save("windows_service_state", state)
        return state

    def state(self) -> dict:
        return self.store.load("windows_service_state", {"status": "not_installed"})
