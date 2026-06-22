"""P8 v26.0 - Role Based Access Control."""

class RBAC:
    def __init__(self):
        self._roles = {}

    def assign(self, user: str, role: str):
        self._roles[user] = role

    def role(self, user: str):
        return self._roles.get(user)
