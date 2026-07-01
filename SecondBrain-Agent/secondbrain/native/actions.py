from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from secondbrain.native.voice_de import GermanVoiceCommandParser, GermanVoiceIntent
from secondbrain.native.approval import NativeActionAuditLog, NativeApprovalQueue
from secondbrain.native.chat import NativeChatService


@dataclass(frozen=True, slots=True)
class NativeActionResult:
    ok: bool
    status: str
    intent: str
    command: str = ""
    target: str = ""
    text: str = ""
    requires_confirmation: bool = False
    executed: bool = False
    returncode: int | None = None
    output: str = ""
    error: str = ""
    next_view: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class NativeActionDispatcher:
    """Executes safe native/voice actions for the desktop shell.

    Design constraints:
    - Read-only/status/search actions may run directly.
    - Mutating actions require explicit confirmation.
    - UI navigation actions never spawn subprocesses.
    - Subprocess calls are bounded by timeout and return structured output.
    """

    READ_ONLY_COMMANDS = {
        "native-status",
        "p1-rag-hybrid-search",
        "p1-rag-answer",
        "p1-production",
        "p1-rag-status",
        "p1-vector-provider-audit",
        "p1-golden-eval",
    }
    MUTATING_COMMANDS = {
        "p1-rag-ingest-file",
        "p1-vector-index-repair",
        "memory-note",
    }

    def __init__(self, project_root: str | Path | None = None, timeout_seconds: int = 30):
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.timeout_seconds = int(timeout_seconds)
        self.parser = GermanVoiceCommandParser()

    def parse_and_dispatch(self, text: str, *, confirmed: bool = False, dry_run: bool = False) -> NativeActionResult:
        return self.dispatch(self.parser.parse(text), confirmed=confirmed, dry_run=dry_run)

    def _finalize(self, result: NativeActionResult, *, confirmed: bool = False, dry_run: bool = False) -> NativeActionResult:
        try:
            NativeActionAuditLog(self.project_root).append(result.to_dict(), confirmed=confirmed, dry_run=dry_run)
        except Exception:
            pass
        return result

    def dispatch(self, intent: GermanVoiceIntent, *, confirmed: bool = False, dry_run: bool = False) -> NativeActionResult:
        command = intent.command
        if intent.intent == "stop":
            return self._finalize(NativeActionResult(True, "stop_requested", intent.intent, command, intent.target, intent.text, next_view="dashboard"), confirmed=confirmed, dry_run=dry_run)

        if intent.intent == "open" or command.startswith("native-open:"):
            target = intent.target or command.split(":", 1)[-1] or "dashboard"
            return self._finalize(NativeActionResult(True, "navigated", intent.intent, command, target, intent.text, executed=False, next_view=target), confirmed=confirmed, dry_run=dry_run)

        if intent.requires_confirmation and not confirmed:
            approval = NativeApprovalQueue(self.project_root).create(
                command=command,
                intent=intent.intent,
                text=intent.text,
                target=intent.target,
            )
            return self._finalize(NativeActionResult(
                False,
                "confirmation_required",
                intent.intent,
                command,
                intent.target,
                intent.text,
                requires_confirmation=True,
                error=f"Freigabe erforderlich: {approval.get('approval_id')}",
                next_view=intent.target,
            ), confirmed=confirmed, dry_run=dry_run)

        if dry_run:
            return self._finalize(NativeActionResult(True, "dry_run", intent.intent, command, intent.target, intent.text, intent.requires_confirmation, False, next_view=intent.target), confirmed=confirmed, dry_run=True)

        if command == "memory-note":
            return self._finalize(self._write_memory_note(intent), confirmed=confirmed, dry_run=dry_run)

        if command == "p1-rag-answer":
            result = NativeChatService(self.project_root, timeout_seconds=self.timeout_seconds).ask(intent.text)
            return self._finalize(NativeActionResult(
                bool(result.get("ok")),
                "executed" if result.get("ok") else "failed",
                intent.intent,
                command,
                intent.target,
                intent.text,
                False,
                True,
                output=str(result.get("answer") or result.get("summary") or ""),
                error=str(result.get("error") or ""),
                next_view="chat",
            ), confirmed=confirmed, dry_run=dry_run)

        if command == "p1-rag-hybrid-search":
            result = NativeChatService(self.project_root, timeout_seconds=self.timeout_seconds).search(intent.text)
            return self._finalize(NativeActionResult(
                bool(result.get("ok")),
                "executed" if result.get("ok") else "failed",
                intent.intent,
                command,
                intent.target,
                intent.text,
                False,
                True,
                output=str(result.get("summary") or result.get("answer") or ""),
                error=str(result.get("error") or ""),
                next_view="chat",
            ), confirmed=confirmed, dry_run=dry_run)

        if command in self.READ_ONLY_COMMANDS or command in self.MUTATING_COMMANDS:
            return self._finalize(self._run_launcher(intent, confirmed=confirmed), confirmed=confirmed, dry_run=dry_run)

        return self._finalize(NativeActionResult(False, "unsupported_command", intent.intent, command, intent.target, intent.text, error=f"Nicht unterstützter Befehl: {command}", next_view=intent.target), confirmed=confirmed, dry_run=dry_run)

    def _run_launcher(self, intent: GermanVoiceIntent, *, confirmed: bool) -> NativeActionResult:
        args = [sys.executable, "launcher.py", intent.command]
        if intent.command in {"p1-rag-hybrid-search", "p1-rag-answer", "p1-rag-ingest-file"} and intent.text:
            args.append(intent.text)
        try:
            proc = subprocess.run(
                args,
                cwd=str(self.project_root),
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
            )
            out = (proc.stdout or proc.stderr or "").strip()
            return NativeActionResult(
                ok=proc.returncode == 0,
                status="executed" if proc.returncode == 0 else "failed",
                intent=intent.intent,
                command=intent.command,
                target=intent.target,
                text=intent.text,
                requires_confirmation=intent.requires_confirmation,
                executed=True,
                returncode=proc.returncode,
                output=out,
                next_view=intent.target,
            )
        except subprocess.TimeoutExpired as exc:
            return NativeActionResult(False, "timeout", intent.intent, intent.command, intent.target, intent.text, intent.requires_confirmation, True, error=str(exc), next_view=intent.target)
        except Exception as exc:  # pragma: no cover - defensive native boundary
            return NativeActionResult(False, "error", intent.intent, intent.command, intent.target, intent.text, intent.requires_confirmation, True, error=f"{type(exc).__name__}: {exc}", next_view=intent.target)

    def _write_memory_note(self, intent: GermanVoiceIntent) -> NativeActionResult:
        path = self.project_root / "runtime" / "native" / "voice_notes.jsonl"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            record = {"kind": "voice_note", "language": "de-DE", "text": intent.text, "source": "native_voice"}
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            return NativeActionResult(True, "executed", intent.intent, intent.command, intent.target, intent.text, True, True, output=f"Notiz gespeichert: {path}", next_view="memory")
        except Exception as exc:
            return NativeActionResult(False, "error", intent.intent, intent.command, intent.target, intent.text, True, True, error=f"{type(exc).__name__}: {exc}", next_view="memory")
