"""Role based access control used by the native workspace.

The original two-method API (``assign``/``role``) remains available.  When a
store is supplied, users, roles and assignments are persisted in the existing
desktop data store.
"""
from __future__ import annotations

from typing import Any, Protocol


class _Store(Protocol):
    def load(self, name: str, default: Any) -> Any: ...

    def save(self, name: str, value: Any) -> None: ...


DEFAULT_ROLES: dict[str, list[str]] = {
    "admin": ["project.read", "project.write", "project.archive", "project.delete", "workspace.manage", "user.manage", "export"],
    "editor": ["project.read", "project.write", "project.archive", "export"],
    "viewer": ["project.read", "export"],
}


class RBAC:
    def __init__(self, store: _Store | None = None):
        self.store = store
        self._roles: dict[str, str] = dict(self._load("access_assignments", {}))

    def _load(self, name: str, default: Any) -> Any:
        return self.store.load(name, default) if self.store is not None else default

    def _save(self, name: str, value: Any) -> None:
        if self.store is not None:
            self.store.save(name, value)

    def roles(self) -> dict[str, list[str]]:
        stored = self._load("access_roles", {})
        merged = {name: list(rights) for name, rights in DEFAULT_ROLES.items()}
        if isinstance(stored, dict):
            for name, rights in stored.items():
                if isinstance(rights, list):
                    merged[str(name)] = sorted({str(right).strip() for right in rights if str(right).strip()})
        return merged

    def add_role(self, name: str, permissions: list[str] | tuple[str, ...]) -> dict[str, Any]:
        role = name.strip().lower()
        if not role:
            raise ValueError("role name must not be empty")
        rights = sorted({str(permission).strip() for permission in permissions if str(permission).strip()})
        custom = self._load("access_roles", {})
        custom = dict(custom) if isinstance(custom, dict) else {}
        custom[role] = rights
        self._save("access_roles", custom)
        return {"name": role, "permissions": rights}

    def users(self) -> list[dict[str, Any]]:
        stored = self._load("access_users", [])
        return [dict(item) for item in stored if isinstance(item, dict)] if isinstance(stored, list) else []

    def add_user(self, user: str, *, display_name: str | None = None, role: str = "viewer") -> dict[str, Any]:
        user_id = user.strip()
        if not user_id:
            raise ValueError("user must not be empty")
        role_name = role.strip().lower()
        if role_name not in self.roles():
            raise ValueError(f"unknown role: {role_name}")
        users = self.users()
        if any(str(item.get("id")) == user_id for item in users):
            raise ValueError(f"user already exists: {user_id}")
        record = {"id": user_id, "display_name": (display_name or user_id).strip(), "active": True}
        users.append(record)
        self._save("access_users", users)
        self.assign(user_id, role_name)
        return {**record, "role": role_name, "permissions": self.permissions(user_id)}

    def assign(self, user: str, role: str) -> None:
        user_id = user.strip()
        role_name = role.strip().lower()
        if not user_id:
            raise ValueError("user must not be empty")
        if role_name not in self.roles():
            raise ValueError(f"unknown role: {role_name}")
        self._roles[user_id] = role_name
        self._save("access_assignments", self._roles)

    def role(self, user: str) -> str | None:
        return self._roles.get(user)

    def permissions(self, user: str) -> list[str]:
        role = self.role(user)
        return list(self.roles().get(role or "", []))

    def allowed(self, user: str, permission: str) -> bool:
        return permission in self.permissions(user)

    def snapshot(self) -> dict[str, Any]:
        users = [{**item, "role": self.role(str(item.get("id", ""))), "permissions": self.permissions(str(item.get("id", "")))} for item in self.users()]
        return {"users": users, "roles": self.roles(), "assignments": dict(self._roles)}
