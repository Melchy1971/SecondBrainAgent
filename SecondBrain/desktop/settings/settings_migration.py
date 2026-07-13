from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


MigrationFn = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class SettingsMigration:
    from_version: str
    to_version: str
    apply: MigrationFn


class SettingsMigrationService:
    def __init__(self) -> None:
        self._migrations: list[SettingsMigration] = []

    def register(self, migration: SettingsMigration) -> None:
        self._migrations.append(migration)

    def migrate(self, settings: dict[str, Any], from_version: str, to_version: str) -> dict[str, Any]:
        current = from_version
        result = dict(settings)
        guard = 0
        while current != to_version:
            guard += 1
            if guard > 100:
                raise RuntimeError("migration cycle detected")
            migration = next((item for item in self._migrations if item.from_version == current), None)
            if migration is None:
                raise ValueError(f"missing migration from {current} to {to_version}")
            result = migration.apply(dict(result))
            current = migration.to_version
        return result
