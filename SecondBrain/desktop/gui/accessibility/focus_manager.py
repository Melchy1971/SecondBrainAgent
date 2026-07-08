from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class FocusManager:
    order: list[str] = field(default_factory=list)
    active: str | None = None

    def register(self, element_id: str) -> None:
        if element_id and element_id not in self.order:
            self.order.append(element_id)
            if self.active is None:
                self.active = element_id

    def focus(self, element_id: str) -> bool:
        if element_id not in self.order:
            return False
        self.active = element_id
        return True

    def next(self) -> str | None:
        if not self.order:
            return None
        if self.active not in self.order:
            self.active = self.order[0]
            return self.active
        idx = (self.order.index(self.active) + 1) % len(self.order)
        self.active = self.order[idx]
        return self.active

    def previous(self) -> str | None:
        if not self.order:
            return None
        if self.active not in self.order:
            self.active = self.order[-1]
            return self.active
        idx = (self.order.index(self.active) - 1) % len(self.order)
        self.active = self.order[idx]
        return self.active
