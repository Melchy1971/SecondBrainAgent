import base64
from datetime import datetime, timezone
from uuid import uuid4


class SecretsVault:
    """
    Local deterministic vault scaffold.
    Uses base64 placeholder encoding, not production encryption.
    Replace with DPAPI/Keyring/Age/SOPS before storing real secrets.
    """
    def __init__(self, store):
        self.store = store

    def put(self, name: str, value: str, scope: str = "default") -> dict:
        secrets = self.store.load("secrets", [])
        encoded = base64.b64encode(value.encode("utf-8")).decode("ascii")
        item = {
            "id": str(uuid4()),
            "name": name,
            "scope": scope,
            "value_enc": encoded,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "active",
        }
        secrets = [s for s in secrets if not (s["name"] == name and s["scope"] == scope)]
        secrets.append(item)
        self.store.save("secrets", secrets)
        return {"id": item["id"], "name": name, "scope": scope, "status": "stored"}

    def list(self) -> list[dict]:
        return [{k: v for k, v in s.items() if k != "value_enc"} for s in self.store.load("secrets", [])]

    def rotate(self, name: str, new_value: str, scope: str = "default") -> dict:
        old = self.store.load("secrets", [])
        for item in old:
            if item["name"] == name and item["scope"] == scope:
                item["status"] = "rotated"
                item["rotated_at"] = datetime.now(timezone.utc).isoformat()
        self.store.save("secrets", old)
        return self.put(name, new_value, scope)
