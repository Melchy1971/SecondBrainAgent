from pathlib import Path
from .store import JsonStore
from .service.windows_service import WindowsServiceManager
from .service.watchdog import Watchdog
from .security.secrets import SecretsVault
from .security.audit import AuditTrail
from .security.approval import ApprovalWorkflow
from .observability.health import HealthEndpoint
from .observability.metrics import MetricsCollector
from .backup.manager import BackupManager
from .deployment.installer import DeploymentPlanner


class ProductionCore:
    def __init__(self, root="."):
        self.root = Path(root)
        self.store = JsonStore(root)
        self.service = WindowsServiceManager(self.store)
        self.watchdog = Watchdog(self.store)
        self.vault = SecretsVault(self.store)
        self.audit = AuditTrail(self.store)
        self.approvals = ApprovalWorkflow(self.store, self.audit)
        self.health_endpoint = HealthEndpoint(self.store, self.watchdog, self.service, self.vault)
        self.metrics = MetricsCollector(self.store)
        self.backups = BackupManager(self.root, self.store)
        self.deployment = DeploymentPlanner(self.store)

    def start_runtime(self) -> dict:
        state = {"status": "running"}
        self.store.save("runtime_state", state)
        self.watchdog.heartbeat("runtime")
        self.audit.log("system", "runtime.start", "production_core")
        return state

    def stop_runtime(self) -> dict:
        state = {"status": "stopped"}
        self.store.save("runtime_state", state)
        self.audit.log("system", "runtime.stop", "production_core")
        return state

    def status(self) -> dict:
        return {
            "version": "15.0",
            "runtime": self.store.load("runtime_state", {"status": "stopped"}),
            "service": self.service.state(),
            "health": self.health_endpoint.health(),
            "metrics": self.metrics.snapshot(),
        }
