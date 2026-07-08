"""v28.0 - General Availability Release Gate."""

class GeneralAvailabilityGate:
    REQUIRED = [
        "provider_registry",
        "installer_manager",
        "e2e_suite",
        "telemetry_center",
        "release_candidate",
    ]

    def evaluate(self, capabilities: dict[str, bool]):
        checks = {k: capabilities.get(k, False) for k in self.REQUIRED}
        return {
            "status": "PASS" if all(checks.values()) else "FAIL",
            "checks": checks,
        }
