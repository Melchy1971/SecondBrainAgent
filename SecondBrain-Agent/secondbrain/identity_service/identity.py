from datetime import datetime, timezone
from uuid import uuid4


class IdentityService:
    def __init__(self, store):
        self.store = store

    def create_local_account(self, display_name: str) -> dict:
        account = {
            "id": str(uuid4()),
            "display_name": display_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "auth_methods": ["local"],
        }
        self.store.save("account", account)
        return account

    def account(self) -> dict:
        return self.store.load("account", {"id": None, "display_name": "local-user", "auth_methods": ["local"]})

    def rotate_token(self, device_id: str) -> dict:
        token = {
            "device_id": device_id,
            "token_id": str(uuid4()),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
        }
        return self.store.append("tokens", token)

    def tokens(self) -> list[dict]:
        return self.store.load("tokens", [])
