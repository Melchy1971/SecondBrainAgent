"""Synchronous, dependency-injected in-process domain event bus."""

from __future__ import annotations

import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Callable

from .domain_events import DomainEvent, sanitize_metadata


EventHandler = Callable[[DomainEvent], None]
EventType = str | type[DomainEvent]


@dataclass(frozen=True)
class PublishResult:
    accepted: bool
    dispatched_handlers: int = 0
    handler_errors: int = 0
    blocked_reason: str = ""

    @property
    def ok(self) -> bool:
        return self.accepted and self.handler_errors == 0


class EventBus:
    """Dispatch events synchronously while isolating consumers from producers."""

    def __init__(self, *, max_processing_depth: int = 16) -> None:
        if max_processing_depth < 1:
            raise ValueError("event_bus_max_depth_must_be_positive")
        self.max_processing_depth = max_processing_depth
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._error_audit: list[dict[str, str | int]] = []
        self._lock = threading.RLock()
        self._local = threading.local()

    def subscribe(self, event_type: EventType, handler: EventHandler) -> EventHandler:
        key = self._event_type_name(event_type)
        if not callable(handler):
            raise TypeError("event_handler_must_be_callable")
        with self._lock:
            if handler not in self._handlers[key]:
                self._handlers[key].append(handler)
        return handler

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> bool:
        key = self._event_type_name(event_type)
        with self._lock:
            handlers = self._handlers.get(key, [])
            if handler not in handlers:
                return False
            handlers.remove(handler)
            if not handlers:
                self._handlers.pop(key, None)
            return True

    def publish(self, event: DomainEvent) -> PublishResult:
        if not isinstance(event, DomainEvent):
            raise TypeError("domain_event_required")
        stack = self._processing_stack()
        if len(stack) >= self.max_processing_depth:
            reason = "max_processing_depth_exceeded"
            self._audit_failure(event, reason, handler="event_bus", depth=len(stack))
            return PublishResult(False, blocked_reason=reason)
        if any(event.event_id == event_id or event.event_type == event_type for event_id, event_type in stack):
            reason = "cyclic_event_processing_blocked"
            self._audit_failure(event, reason, handler="event_bus", depth=len(stack))
            return PublishResult(False, blocked_reason=reason)

        with self._lock:
            handlers = tuple(self._handlers.get(event.event_type, ()))
        stack.append((event.event_id, event.event_type))
        failures = 0
        try:
            for handler in handlers:
                try:
                    handler(event)
                except Exception as exc:  # noqa: BLE001 - subscriber failures are isolated by design
                    failures += 1
                    self._audit_failure(
                        event,
                        f"{type(exc).__name__}:{exc}",
                        handler=self._handler_name(handler),
                        depth=len(stack),
                    )
        finally:
            stack.pop()
        return PublishResult(True, dispatched_handlers=len(handlers), handler_errors=failures)

    @property
    def error_audit(self) -> tuple[dict[str, str | int], ...]:
        with self._lock:
            return tuple(dict(row) for row in self._error_audit)

    @property
    def audit_log(self) -> tuple[dict[str, str | int], ...]:
        """Compatibility alias for diagnostics that use generic audit naming."""

        return self.error_audit

    def _audit_failure(self, event: DomainEvent, error: str, *, handler: str, depth: int) -> None:
        safe_error = str(sanitize_metadata({"error": error}).get("error") or "event_handler_error")
        record: dict[str, str | int] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event_id": event.event_id,
            "event_type": event.event_type,
            "correlation_id": event.correlation_id,
            "handler": handler,
            "error": safe_error,
            "depth": depth,
        }
        with self._lock:
            self._error_audit.append(record)

    def _processing_stack(self) -> list[tuple[str, str]]:
        stack = getattr(self._local, "stack", None)
        if stack is None:
            stack = []
            self._local.stack = stack
        return stack

    @staticmethod
    def _event_type_name(event_type: EventType) -> str:
        if isinstance(event_type, str):
            normalized = event_type.strip()
        elif isinstance(event_type, type) and issubclass(event_type, DomainEvent):
            normalized = event_type.EVENT_TYPE
        else:
            raise TypeError("invalid_domain_event_type")
        if not normalized:
            raise ValueError("event_type_required")
        return normalized

    @staticmethod
    def _handler_name(handler: EventHandler) -> str:
        return str(getattr(handler, "__qualname__", getattr(handler, "__name__", type(handler).__name__)))

