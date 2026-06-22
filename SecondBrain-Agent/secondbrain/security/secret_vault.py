"""P8 v26.0 - Secret Vault Foundation."""

class SecretVault:
    def __init__(self):
        self._secrets = {}

    def put(self, key: str, value: str):
        self._secrets[key] = value

    def get(self, key: str):
        return self._secrets.get(key)
