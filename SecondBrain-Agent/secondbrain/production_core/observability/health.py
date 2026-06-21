class HealthEndpoint:
    def __init__(self, store, watchdog, service, vault):
        self.store = store
        self.watchdog = watchdog
        self.service = service
        self.vault = vault

    def health(self) -> dict:
        scan = self.watchdog.scan()
        return {
            "status": scan["status"],
            "watchdog": scan,
            "service": self.service.state(),
            "secrets": len(self.vault.list()),
        }

    def ready(self) -> dict:
        health = self.health()
        return {
            "ready": health["status"] in {"healthy", "degraded"},
            "health": health,
        }
