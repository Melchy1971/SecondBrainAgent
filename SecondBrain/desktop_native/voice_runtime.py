from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

from .action_registry import ActionDefinition, ActionRegistry


class VoiceState(StrEnum):
    IDLE = "IDLE"
    LISTENING_FOR_WAKE_WORD = "LISTENING_FOR_WAKE_WORD"
    LISTENING = "LISTENING"
    TRANSCRIBING = "TRANSCRIBING"
    UNDERSTANDING = "UNDERSTANDING"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    EXECUTING = "EXECUTING"
    SPEAKING = "SPEAKING"
    ERROR = "ERROR"
    MUTED = "MUTED"


@dataclass(slots=True)
class DialogContext:
    action_id: str
    parameters: dict[str, Any]
    missing_parameters: list[str]
    workspace_id: str
    actor: str
    confirmation_state: str = "pending"
    approval_state: str = "not_required"
    expires_at: float = field(default_factory=lambda: time.time() + 120)
    binding: str = ""


class VoiceSession:
    """Thread-safe orchestration; audio engines remain replaceable adapters."""

    CONFIRMATIONS = {"ja", "bestätigen", "bestaetigen", "ausführen", "ausfuehren"}
    CANCELLATIONS = {"abbrechen", "abbruch", "stopp", "stop"}

    def __init__(self, registry: ActionRegistry, *, workspace_id: str = "", actor: str = "local-user") -> None:
        self.registry = registry
        self.workspace_id = workspace_id
        self.actor = actor
        self.state = VoiceState.IDLE
        self.dialog: DialogContext | None = None
        self._lock = threading.RLock()
        self.tts_active = False

    def push_to_talk(self) -> VoiceState:
        with self._lock:
            if self.state != VoiceState.MUTED and not self.tts_active:
                self.state = VoiceState.LISTENING
            return self.state

    def set_audio_state(self, state: VoiceState | str) -> VoiceState:
        """Accept lifecycle updates only from the replaceable audio adapter."""
        next_state = VoiceState(state)
        if next_state not in {VoiceState.IDLE, VoiceState.LISTENING, VoiceState.TRANSCRIBING, VoiceState.ERROR}:
            raise ValueError(f"invalid audio state: {next_state}")
        with self._lock:
            if self.state == VoiceState.MUTED or self.tts_active:
                return self.state
            self.state = next_state
            return self.state

    def listen_for_wake_word(self, enabled: bool = True) -> VoiceState:
        with self._lock:
            if self.state != VoiceState.MUTED and not self.tts_active:
                self.state = VoiceState.LISTENING_FOR_WAKE_WORD if enabled else VoiceState.IDLE
            return self.state

    def mute(self, enabled: bool = True) -> VoiceState:
        with self._lock:
            self.state = VoiceState.MUTED if enabled else VoiceState.IDLE
            return self.state

    def wake(self, phrase: str) -> bool:
        with self._lock:
            if self.tts_active or self.state == VoiceState.MUTED:
                return False
            matched = phrase.casefold().strip() in {"jarvis", "hey jarvis", "secondbrain"}
            if matched:
                self.state = VoiceState.LISTENING
            return matched

    def understand(self, utterance: str, parameters: Mapping[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            self.state = VoiceState.UNDERSTANDING
            normalized = " ".join(utterance.casefold().strip().split())
            if normalized in self.CONFIRMATIONS:
                return self._confirm()
            action = self.registry.resolve_alias(utterance) or self.registry.get("assistant.ask")
            values = dict(parameters or {})
            values.update({name: schema["const"] for name, schema in action.parameters.items() if "const" in schema})
            if action.id == "assistant.ask":
                values.setdefault("text", utterance.strip())
            missing = [name for name, schema in action.parameters.items()
                       if schema.get("const") is None and schema.get("minLength", 0) > 0 and not values.get(name)]
            if action.requires_workspace and not self.workspace_id:
                return self._error("workspace_required")
            if missing:
                self.dialog = self._context(action, values, missing)
                self.state = VoiceState.WAITING_FOR_CONFIRMATION
                return self._slots_required(action.id)
            if action.requires_approval:
                self.dialog = self._context(action, values, [])
                self.dialog.approval_state = "pending"
                self.state = VoiceState.WAITING_FOR_APPROVAL
                return {"status": "approval_required", "action_id": action.id, "binding": self.dialog.binding}
            if action.requires_confirmation:
                self.dialog = self._context(action, values, [])
                self.state = VoiceState.WAITING_FOR_CONFIRMATION
                return {"status": "confirmation_required", "action_id": action.id, "binding": self.dialog.binding}
            return self._execute(action, values)

    def dispatch(self, action_id: str, parameters: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Dispatch a trusted adapter mapping while preserving all registry policies."""
        with self._lock:
            return self._dispatch(action_id, parameters)

    def _dispatch(self, action_id: str, parameters: Mapping[str, Any] | None = None) -> dict[str, Any]:
        self.state = VoiceState.UNDERSTANDING
        action = self.registry.get(action_id)
        values = dict(parameters or {})
        values.update({name: schema["const"] for name, schema in action.parameters.items() if "const" in schema})
        missing = [name for name, schema in action.parameters.items()
                   if schema.get("const") is None and schema.get("minLength", 0) > 0 and not values.get(name)]
        if action.requires_workspace and not self.workspace_id:
            return self._error("workspace_required")
        if missing:
            self.dialog = self._context(action, values, missing)
            self.state = VoiceState.WAITING_FOR_CONFIRMATION
            return self._slots_required(action.id)
        if action.requires_approval:
            self.dialog = self._context(action, values, [])
            self.state = VoiceState.WAITING_FOR_APPROVAL
            return {"status": "approval_required", "action_id": action.id, "binding": self.dialog.binding}
        if action.requires_confirmation:
            self.dialog = self._context(action, values, [])
            self.state = VoiceState.WAITING_FOR_CONFIRMATION
            return {"status": "confirmation_required", "action_id": action.id, "binding": self.dialog.binding}
        return self._execute(action, values)

    def provide_slots(self, parameters: Mapping[str, Any]) -> dict[str, Any]:
        with self._lock:
            if not self.dialog or self.dialog.expires_at < time.time():
                return self._error("no_active_dialog")
            if self.dialog.workspace_id != self.workspace_id:
                return self._error("dialog_workspace_mismatch")
            action = self.registry.get(self.dialog.action_id)
            self.dialog.parameters.update(parameters)
            self.dialog.missing_parameters = [
                name for name in self.dialog.missing_parameters if not self.dialog.parameters.get(name)
            ]
            if self.dialog.missing_parameters:
                return self._slots_required(action.id)
            self.dialog = self._context(action, self.dialog.parameters, [])
            self.state = VoiceState.WAITING_FOR_APPROVAL if action.requires_approval else VoiceState.WAITING_FOR_CONFIRMATION
            return {
                "status": "approval_required" if action.requires_approval else "confirmation_required",
                "action_id": action.id,
                "binding": self.dialog.binding,
            }

    def continue_dialog(self, utterance: str) -> dict[str, Any]:
        with self._lock:
            normalized = " ".join(str(utterance).casefold().strip().split())
            if not self.dialog or self.dialog.expires_at < time.time():
                return self._error("no_active_dialog")
            if self.dialog.workspace_id != self.workspace_id:
                return self._error("dialog_workspace_mismatch")
            if normalized in self.CANCELLATIONS:
                action_id = self.dialog.action_id
                self.dialog = None
                self.state = VoiceState.IDLE
                return {"status": "dialog_cancelled", "action_id": action_id}
            if normalized in self.CONFIRMATIONS or not normalized:
                return self._error("slot_value_required")
            if not self.dialog.missing_parameters:
                return self._error("no_missing_slots")
            return self.provide_slots({self.dialog.missing_parameters[0]: utterance.strip()})

    def _slots_required(self, action_id: str) -> dict[str, Any]:
        missing = list(self.dialog.missing_parameters) if self.dialog else []
        return {
            "status": "slots_required",
            "missing": missing,
            "action_id": action_id,
        }

    def _context(self, action: ActionDefinition, values: dict[str, Any], missing: list[str]) -> DialogContext:
        raw = json.dumps({"action": action.id, "parameters": values, "workspace": self.workspace_id}, sort_keys=True)
        return DialogContext(action.id, values, missing, self.workspace_id, self.actor,
                             approval_state="pending" if action.requires_approval else "not_required",
                             binding=hashlib.sha256(raw.encode()).hexdigest())

    def _confirm(self) -> dict[str, Any]:
        if not self.dialog or self.dialog.expires_at < time.time() or self.dialog.missing_parameters:
            return self._error("no_bound_confirmation")
        action = self.registry.get(self.dialog.action_id)
        if action.requires_approval:
            self.state = VoiceState.WAITING_FOR_APPROVAL
            return {"status": "approval_required", "action_id": action.id, "binding": self.dialog.binding}
        return self._execute(action, self.dialog.parameters)

    def approve(self, binding: str) -> dict[str, Any]:
        with self._lock:
            if not self.dialog or binding != self.dialog.binding or self.dialog.workspace_id != self.workspace_id:
                return self._error("approval_binding_mismatch")
            action = self.registry.get(self.dialog.action_id)
            self.dialog.approval_state = "approved"
            return self._execute(action, self.dialog.parameters)

    def _execute(self, action: ActionDefinition, values: Mapping[str, Any]) -> dict[str, Any]:
        if not action.is_available():
            return self._error("action_unavailable")
        self.state = VoiceState.EXECUTING
        try:
            result = action.handler({**values, "workspace_id": self.workspace_id, "actor": self.actor})
            self.dialog = None
            self.state = VoiceState.IDLE
            return {"status": "executed", "action_id": action.id, "result": result}
        except Exception as exc:
            return self._error(f"{type(exc).__name__}: {exc}")

    def _error(self, message: str) -> dict[str, Any]:
        self.state = VoiceState.ERROR
        return {"status": "error", "error": message}

    def set_speaking(self, enabled: bool) -> None:
        with self._lock:
            self.tts_active = enabled
            self.state = VoiceState.SPEAKING if enabled else VoiceState.IDLE
