from __future__ import annotations

from dataclasses import dataclass, field

from .security_models import SettingsAuditAction, SettingsAuditEntry


@dataclass
class SettingsAuditLog:
    entries: list[SettingsAuditEntry] = field(default_factory=list)

    def record(self, action: SettingsAuditAction | str, key: str, before=None, after=None, actor: str = "system", metadata: dict | None = None) -> SettingsAuditEntry:
        entry = SettingsAuditEntry(
            action=SettingsAuditAction(action),
            key=key,
            actor=actor,
            before=before,
            after=after,
            metadata=dict(metadata or {}),
        )
        self.entries.append(entry)
        return entry

    def by_key(self, key: str) -> list[SettingsAuditEntry]:
        return [entry for entry in self.entries if entry.key == key]

    def export(self) -> list[dict]:
        return [entry.to_dict() for entry in self.entries]
