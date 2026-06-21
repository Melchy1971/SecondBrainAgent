from datetime import datetime, timezone
from uuid import uuid4
from pathlib import Path
import shutil


class BackupManager:
    def __init__(self, root, store):
        self.root = Path(root)
        self.store = store
        self.backup_dir = self.root / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create(self, label: str = "manual") -> dict:
        backup_id = str(uuid4())
        target = self.backup_dir / backup_id
        target.mkdir(parents=True, exist_ok=True)
        data_dir = self.root / "data"
        if data_dir.exists():
            shutil.copytree(data_dir, target / "data", dirs_exist_ok=True)
        item = {
            "id": backup_id,
            "label": label,
            "path": str(target),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "created",
        }
        self.store.append("backups", item)
        return item

    def verify(self, backup_id: str) -> dict:
        backups = self.store.load("backups", [])
        backup = next((b for b in backups if b["id"] == backup_id), None)
        if not backup:
            return {"ok": False, "error": "backup_not_found"}
        exists = Path(backup["path"]).exists()
        return {"ok": exists, "backup_id": backup_id, "path": backup["path"], "status": "verified" if exists else "missing"}

    def list(self) -> list[dict]:
        return self.store.load("backups", [])

    def restore_plan(self, backup_id: str) -> dict:
        verification = self.verify(backup_id)
        return {
            "backup_id": backup_id,
            "can_restore": verification.get("ok", False),
            "steps": [
                "stop_runtime",
                "copy_current_data_to_pre_restore_backup",
                "restore_backup_data",
                "run_healthcheck",
                "start_runtime",
            ],
            "verification": verification,
        }
