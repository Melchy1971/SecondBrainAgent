"""Voice GUI: microphone status, audio level, and privacy/enable controls.

Headless ``VoiceStatusController`` (unit-testable) plus a lazy Tkinter panel. The
assistant runs its capture loop on a worker thread and pushes status snapshots to
the UI via a scheduler, so the GUI never blocks and always shows a live mic state
even when no microphone is present.
"""

from __future__ import annotations

from typing import Any, Callable

from secondbrain.voice.assistant import ContinuousVoiceAssistant, VoiceStatus


class VoiceStatusController:
    def __init__(self, assistant: ContinuousVoiceAssistant) -> None:
        self.assistant = assistant

    def snapshot(self) -> dict[str, Any]:
        return self.assistant.status().to_dict()

    def toggle_enabled(self) -> dict[str, Any]:
        self.assistant.set_enabled(not self.assistant.config.enabled)
        return self.snapshot()

    def toggle_privacy(self) -> dict[str, Any]:
        self.assistant.set_privacy(not self.assistant.config.privacy_mode)
        return self.snapshot()

    def toggle_offline(self) -> dict[str, Any]:
        self.assistant.set_offline(not self.assistant.config.offline)
        return self.snapshot()

    def start(self) -> bool:
        return self.assistant.start()

    def stop(self) -> None:
        self.assistant.stop()


_STATUS_COLOR = {
    "ok": "#0a7a2f", "missing": "#b00020", "error": "#b00020",
    "muted": "#a05a00", "disabled": "#666666",
}


def build_panel(master: Any, assistant: ContinuousVoiceAssistant,
                *, scheduler: Callable[[Callable[[], None]], None] | None = None) -> Any:
    """Build the Tk voice status frame. Requires a display."""
    import tkinter as tk
    from tkinter import ttk

    controller = VoiceStatusController(assistant)
    frame = ttk.Frame(master, padding=8)

    mic_var = tk.StringVar()
    state_var = tk.StringVar()
    level = ttk.Progressbar(frame, orient="horizontal", length=200, maximum=100)

    ttk.Label(frame, text="Mikrofon:").grid(row=0, column=0, sticky="w")
    mic_label = ttk.Label(frame, textvariable=mic_var)
    mic_label.grid(row=0, column=1, sticky="w")
    ttk.Label(frame, text="Status:").grid(row=1, column=0, sticky="w")
    ttk.Label(frame, textvariable=state_var).grid(row=1, column=1, sticky="w")
    ttk.Label(frame, text="Pegel:").grid(row=2, column=0, sticky="w")
    level.grid(row=2, column=1, sticky="w", pady=4)

    enabled_var = tk.BooleanVar(value=assistant.config.enabled)
    privacy_var = tk.BooleanVar(value=assistant.config.privacy_mode)
    offline_var = tk.BooleanVar(value=assistant.config.offline)

    def render(snap: dict) -> None:
        mic_var.set(snap["mic_status"])
        mic_label.configure(foreground=_STATUS_COLOR.get(snap["mic_status"], "#000000"))
        state_var.set(snap["state"] + ("  |  " + snap["last_error"] if snap["last_error"] else ""))
        level.configure(value=snap["level"] * 100)
        enabled_var.set(snap["enabled"])
        privacy_var.set(snap["privacy"])
        offline_var.set(snap["offline"])

    def on_status(status: VoiceStatus) -> None:
        sched = scheduler or frame.after
        sched(lambda: render(status.to_dict()))

    assistant.on_status = on_status

    ttk.Checkbutton(frame, text="Voice aktiv", variable=enabled_var,
                    command=lambda: render(controller.toggle_enabled())).grid(row=3, column=0, sticky="w", pady=(8, 0))
    ttk.Checkbutton(frame, text="Privacy (Mute)", variable=privacy_var,
                    command=lambda: render(controller.toggle_privacy())).grid(row=3, column=1, sticky="w", pady=(8, 0))
    ttk.Checkbutton(frame, text="Offline", variable=offline_var,
                    command=lambda: render(controller.toggle_offline())).grid(row=4, column=0, sticky="w")

    render(controller.snapshot())
    return frame
