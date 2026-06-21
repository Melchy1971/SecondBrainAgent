class DeploymentPlanner:
    def __init__(self, store):
        self.store = store

    def installer_manifest(self) -> dict:
        manifest = {
            "name": "SecondBrain OS",
            "version": "15.0",
            "targets": ["portable", "windows_service", "docker_future"],
            "entrypoints": {
                "cli": "python launcher.py",
                "service": "python launcher.py prod-service-run",
                "health": "python launcher.py prod-health",
            },
            "required_files": ["launcher.py", "secondbrain/", "config/", "requirements.txt"],
        }
        self.store.save("installer_manifest", manifest)
        return manifest

    def migration_plan(self, from_version: str, to_version: str = "15.0") -> dict:
        plan = {
            "from_version": from_version,
            "to_version": to_version,
            "steps": ["backup", "validate_config", "copy_files", "migrate_data", "run_tests", "healthcheck"],
            "rollback": ["restore_backup", "restart_previous_runtime"],
        }
        self.store.save("migration_plan", plan)
        return plan
