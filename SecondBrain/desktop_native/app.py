from __future__ import annotations

import json
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from secondbrain.desktop_native.action_bus import NativeActionBus
from secondbrain.desktop_native.alert_surface import live_alert_labels, queue_activity
from secondbrain.desktop_native.approval_surface import ApprovalSurface, approval_activity, approval_notification
from secondbrain.desktop_native.dialog_prompts import dialog_prompt
from secondbrain.desktop_native.hotkey import GlobalPushToTalkHotkey
from secondbrain.desktop_native.job_surface import JobSurface
from secondbrain.desktop_native.lifecycle import InstanceAlreadyRunning, SingleInstanceLock, WindowStateStore
from secondbrain.desktop_native.navigation import VIEWS, display_view
from secondbrain.desktop_native.runtime_diagnostics import runtime_diagnostics, safe_status
from secondbrain.desktop_native.runtime_info import (
    calendar_month,
    release_blocker_count,
    runtime_log_level,
    topbar_status_labels,
)
from secondbrain.desktop_native.status import write_native_status_report
from secondbrain.desktop_native.storage_alerts import read_vector_validation, storage_alert_labels
from secondbrain.desktop_native.system_metrics import (
    SystemMetricsSampler,
    format_bytes,
    format_kbps,
    format_percent,
    format_uptime,
)
from secondbrain.desktop_native.tray import SystemTrayController, tray_status_text
from secondbrain.desktop_native.tts import LocalTtsRuntime
from secondbrain.desktop_native.wake_word import WakeWordConfig, WakeWordRuntime
from secondbrain.desktop_native.vault_surface import vault_status_labels
from secondbrain.desktop_native.weather import fetch_weather, weather_config, weather_labels
from secondbrain.desktop_native.voice_de import GermanVoiceController
from secondbrain.desktop.gui.data_providers import LiveDataService
from secondbrain.gui.backup_center import BackupCenterViewModel
from secondbrain.gui.bootstrap import bootstrap_text
from secondbrain.native.job_queue_center.service import JobQueueService
from secondbrain.version import get_version

VERSION = get_version()
TITLE = f"Jarvis SecondBrain {VERSION} - Native Desktop"

HUD = {
    "bg": "#02060b",
    "bg2": "#040b12",
    "panel": "#071722",
    "panel2": "#091c28",
    "line": "#145c6e",
    "line2": "#0d3442",
    "cyan": "#2fe6ff",
    "cyan_soft": "#bff8ff",
    "cyan_dim": "#5d8597",
    "good": "#3ef0a4",
    "warn": "#ffb24d",
    "bad": "#ff5d6c",
    "text": "#eafcff",
}

NAV_ITEMS = [*VIEWS, "Imports", "Production", "Developer"]


def _fmt_status(value: Any) -> str:
    if value in (None, ""):
        return "-"
    if isinstance(value, bool):
        return "OK" if value else "BLOCKED"
    return str(value)


class JarvisNativeApp(tk.Tk):
    def __init__(self, project_root: str | Path | None = None):
        super().__init__()
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.window_state = WindowStateStore(self.project_root)
        restored = self.window_state.load()
        self.action_bus = NativeActionBus(self.project_root, workspace_id=str(self.project_root))
        self.approval_surface = ApprovalSurface(self.action_bus.approvals, workspace_id=str(self.project_root))
        self.job_surface = JobSurface(JobQueueService(self.project_root))
        self.backup_center = BackupCenterViewModel(self.project_root)
        self.live_data = LiveDataService(self.project_root)
        self.voice = GermanVoiceController(
            self.project_root,
            tts_runtime=LocalTtsRuntime(on_state=self.action_bus.voice.set_speaking),
            on_state=self.action_bus.voice.set_audio_state,
        )
        wake_enabled = os.environ.get("SECONDBRAIN_WAKE_WORD_ENABLED", "").casefold() in {"1", "true", "yes", "on"}
        self.wake_runtime = WakeWordRuntime(
            self.action_bus.voice,
            self._wake_phrase_source,
            config=WakeWordConfig(enabled=wake_enabled),
            on_activation=lambda _phrase: self.after(0, self.listen_once),
        )
        hotkey_enabled = os.environ.get("SECONDBRAIN_GLOBAL_HOTKEY_ENABLED", "").casefold() in {"1", "true", "yes", "on"}
        try:
            self.global_hotkey = GlobalPushToTalkHotkey(
                lambda: self.after(0, self.listen_once),
                hotkey=os.environ.get("SECONDBRAIN_PUSH_TO_TALK_HOTKEY", "<ctrl>+<alt>+j"),
                enabled=hotkey_enabled,
            )
        except ValueError:
            self.global_hotkey = GlobalPushToTalkHotkey(lambda: None)
        self.queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.current_view = tk.StringVar(value="Dashboard")
        self.status_var = tk.StringVar(value="Initialisiere")
        self.voice_var = tk.StringVar(value="Deutsch - bereit fuer Textbefehle")
        self.dialog_tts_enabled = os.environ.get("SECONDBRAIN_DIALOG_TTS_ENABLED", "").casefold() in {
            "1", "true", "yes", "on"
        }
        self.voice_state_var = tk.StringVar(value=self.action_bus.voice.state.value)
        self.clock_time = tk.StringVar(value="")
        self.clock_day = tk.StringVar(value="")
        self.clock_date = tk.StringVar(value="")
        self.clock_month = tk.StringVar(value="")
        self.weather_place = tk.StringVar(value="Weather")
        self.weather_temperature = tk.StringVar(value="Loading")
        self.weather_detail = tk.StringVar(value="")
        self.metric_vars: dict[str, tk.StringVar] = {}
        self.metric_rings: dict[str, tk.Canvas] = {}
        self.system_metrics: dict[str, Any] = {"available": False}
        self.system_metrics_sampler = SystemMetricsSampler()
        self.info_vars: dict[str, tk.StringVar] = {}
        self.alert_vars: dict[str, tk.StringVar] = {}
        self.approval_alert_label: tk.Label | None = None
        self.approval_tray_status = "Unavailable"
        self.approval_pending_count: int | None = None
        self.pill_vars: dict[str, tk.StringVar] = {}
        self.nav_buttons: dict[str, tk.Button] = {}
        self.geometry(str(restored.get("geometry") or "1500x900"))
        self.minsize(1180, 720)
        self.title(TITLE)
        self.configure(bg=HUD["bg"])
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._configure_theme()
        self._build_layout()
        self.tray = SystemTrayController(
            on_open=lambda: self.after(0, self._restore_window),
            on_open_approvals=lambda: self.after(0, self._open_approvals),
            on_toggle_listening=lambda: self.after(0, self._toggle_wake_listening),
            on_toggle_mute=lambda: self.after(0, self._toggle_mute),
            on_push_to_talk=lambda: self.after(0, self.listen_once),
            on_exit=lambda: self.after(0, self._exit_app),
            status_text=lambda: tray_status_text(
                status=self.status_var.get(),
                voice=str(self.action_bus.voice.state),
                approvals=self.approval_tray_status,
            ),
        )
        self.tray.start()
        self.wake_runtime.start()
        self.global_hotkey.start()
        self.after(100, self.refresh_status)
        self.after(5000, self._refresh_system_metrics)
        self.after(1000, self._refresh_queue_status)
        self.after(1100, self._refresh_approval_status)
        self.after(200, self._drain_queue)
        self.after(300, self._request_weather)
        self.after(100, self._sync_voice_state)
        self._tick_clock()

    def _on_close(self) -> None:
        self.window_state.save(geometry=self.geometry(), view=self.current_view.get())
        if self.tray.running:
            self.withdraw()
        else:
            self.destroy()

    def _restore_window(self) -> None:
        self.deiconify()
        self.lift()
        self.focus_force()

    def _open_approvals(self) -> None:
        self._restore_window()
        self.show_view("Approvals")

    def _toggle_mute(self) -> None:
        muted = self.action_bus.voice.state != "MUTED"
        self.action_bus.voice.mute(muted)
        self.voice_var.set("Mikrofon stumm" if muted else "Deutsch - bereit")

    def _toggle_wake_listening(self) -> None:
        enabled = not bool(self.wake_runtime.status()["enabled"])
        self.wake_runtime.enable(enabled)
        self.voice_var.set("Wake Word aktiv" if enabled else "Wake Word aus")

    def _sync_voice_state(self) -> None:
        self.voice_state_var.set(self.action_bus.voice.state.value)
        self.after(100, self._sync_voice_state)

    def _wake_phrase_source(self) -> str:
        result = self.voice.listen_once(timeout=1, phrase_time_limit=2, report_state=False)
        return str(result.get("text") or "")

    def _exit_app(self) -> None:
        self.window_state.save(geometry=self.geometry(), view=self.current_view.get())
        self.global_hotkey.stop()
        self.wake_runtime.stop()
        self.tray.stop()
        self.destroy()

    def _configure_theme(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Hud.Vertical.TScrollbar", background=HUD["panel"], troughcolor=HUD["bg"])

    def _panel(self, parent: tk.Misc, **grid: Any) -> tk.Frame:
        frame = tk.Frame(
            parent,
            bg=HUD["panel"],
            highlightbackground=HUD["line"],
            highlightcolor=HUD["line"],
            highlightthickness=1,
            bd=0,
        )
        frame.grid(**grid)
        return frame

    def _label(
        self,
        parent: tk.Misc,
        text: str = "",
        *,
        fg: str | None = None,
        bg: str | None = None,
        font: tuple[str, int, str] | tuple[str, int] | None = None,
        textvariable: tk.StringVar | None = None,
        anchor: str = "w",
        **pack: Any,
    ) -> tk.Label:
        label = tk.Label(
            parent,
            text=text,
            textvariable=textvariable,
            bg=bg or parent.cget("bg"),
            fg=fg or HUD["cyan_soft"],
            font=font or ("Segoe UI", 10),
            anchor=anchor,
        )
        label.pack(**pack)
        return label

    def _section_title(self, parent: tk.Misc, title: str, meta: str | tk.StringVar = "") -> None:
        bar = tk.Frame(parent, bg=parent.cget("bg"))
        bar.pack(fill="x", padx=14, pady=(12, 7))
        self._label(
            bar,
            title.upper(),
            fg=HUD["cyan"],
            font=("Segoe UI", 10, "bold"),
            side="left",
        )
        if meta:
            meta_text = meta.upper() if isinstance(meta, str) else ""
            meta_variable = meta if isinstance(meta, tk.StringVar) else None
            self._label(
                bar,
                meta_text,
                textvariable=meta_variable,
                fg=HUD["cyan_dim"],
                font=("Segoe UI", 8, "bold"),
                side="right",
            )
        tk.Frame(bar, height=1, bg=HUD["line2"]).pack(fill="x", side="bottom", pady=(8, 0))

    def _kv(self, parent: tk.Misc, key: str, var: tk.StringVar, *, accent: str | None = None) -> tk.Label:
        row = tk.Frame(parent, bg=parent.cget("bg"))
        row.pack(fill="x", padx=14, pady=3)
        self._label(row, key, fg=HUD["cyan_soft"], font=("Segoe UI", 9, "bold"), side="left")
        value_label = self._label(
            row, textvariable=var, fg=accent or HUD["text"], font=("Segoe UI", 9, "bold"), side="right"
        )
        tk.Frame(parent, height=1, bg=HUD["line2"]).pack(fill="x", padx=14)
        return value_label

    def _build_layout(self) -> None:
        root = tk.Frame(self, bg=HUD["bg"])
        root.pack(fill="both", expand=True)
        root.grid_columnconfigure(0, minsize=232)
        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(0, weight=1)

        self._build_sidebar(root)
        main = tk.Frame(root, bg=HUD["bg"])
        main.grid(row=0, column=1, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        self._build_topbar(main)
        self._build_content(main)
        self._build_statusbar(main)

    def _build_sidebar(self, root: tk.Misc) -> None:
        side = tk.Frame(root, bg=HUD["bg2"], highlightbackground=HUD["line2"], highlightthickness=1, bd=0)
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_propagate(False)

        logo = tk.Frame(side, bg=HUD["bg2"])
        logo.pack(fill="x", padx=14, pady=(8, 14))
        mark = tk.Canvas(logo, width=36, height=36, bg=HUD["bg2"], highlightthickness=0)
        mark.pack(side="left")
        mark.create_rectangle(2, 2, 34, 34, outline=HUD["line"], fill=HUD["panel2"], width=1)
        mark.create_oval(11, 11, 25, 25, outline=HUD["cyan"], width=2)
        mark.create_oval(16, 16, 20, 20, fill=HUD["cyan"], outline="")
        brand = tk.Frame(logo, bg=HUD["bg2"])
        brand.pack(side="left", padx=10)
        self._label(brand, "JARVIS", fg=HUD["text"], font=("Segoe UI", 16, "bold"), anchor="w")
        self._label(brand, "SecondBrain Agent", fg=HUD["cyan_dim"], font=("Segoe UI", 7), anchor="w")
        tk.Frame(side, height=1, bg=HUD["line2"]).pack(fill="x", padx=14, pady=(0, 14))

        nav = tk.Frame(side, bg=HUD["bg2"])
        nav.pack(fill="both", expand=True, padx=14)
        for item in NAV_ITEMS:
            button = tk.Button(
                nav,
                text=f"  {item}",
                command=lambda view=item: self.show_view(view),
                anchor="w",
                relief="flat",
                bd=0,
                padx=10,
                pady=8,
                bg=HUD["bg2"],
                fg=HUD["cyan_soft"],
                activebackground=HUD["panel2"],
                activeforeground=HUD["text"],
                font=("Segoe UI", 10, "bold"),
                cursor="hand2",
            )
            button.pack(fill="x", pady=2)
            self.nav_buttons[item] = button
        self._sync_nav()

        quick = tk.Frame(side, bg=HUD["bg2"])
        quick.pack(fill="x", padx=14, pady=(8, 14))
        self._hud_button(quick, "STATUS AKTUALISIEREN", self.refresh_status).pack(fill="x", pady=3)
        self._hud_button(quick, "DATEI IMPORTIEREN", self.import_file).pack(fill="x", pady=3)
        self._hud_button(quick, "BACKUP CENTER", lambda: self.show_view("Backups")).pack(fill="x", pady=3)
        self._hud_button(quick, "REPAIR INDEX", self.repair_index, warn=True).pack(fill="x", pady=3)

    def _build_topbar(self, main: tk.Misc) -> None:
        top = tk.Frame(main, bg=HUD["bg2"], highlightbackground=HUD["line2"], highlightthickness=1, bd=0)
        top.grid(row=0, column=0, sticky="ew")
        title = tk.Frame(top, bg=HUD["bg2"])
        title.pack(side="left", padx=20, pady=9)
        self._label(title, "SECONDBRAIN", fg=HUD["text"], font=("Segoe UI", 18, "bold"), anchor="w")
        self._label(title, f"JARVIS CONTROL CENTER   v{VERSION}", fg=HUD["cyan"], font=("Segoe UI", 8, "bold"), anchor="w")

        self._pill(top, "SYSTEM HEALTH", self.status_var, accent=HUD["good"])
        self._pill(top, "VOICE", self.voice_state_var, accent=HUD["cyan"])
        for key, value, accent in [
            ("RELEASE GATE", "Unknown", HUD["good"]),
            ("EMBEDDING", "Unknown", None),
            ("POSTGRESQL", "Unknown", None),
        ]:
            var = tk.StringVar(value=value)
            self.pill_vars[key] = var
            self._pill(top, key, var, accent=accent)

        user = tk.Frame(top, bg=HUD["bg2"])
        user.pack(side="right", padx=16)
        self._label(user, "Jarvis", fg=HUD["text"], font=("Segoe UI", 9, "bold"), side="left", padx=(0, 10))
        avatar = tk.Label(user, text="J", bg=HUD["panel2"], fg=HUD["cyan"], font=("Segoe UI", 12, "bold"), width=3, height=1)
        avatar.pack(side="left")

    def _pill(self, parent: tk.Misc, key: str, value: tk.StringVar, *, accent: str | None = None) -> None:
        pill = tk.Frame(parent, bg=HUD["panel"], highlightbackground=HUD["line"], highlightthickness=1, bd=0)
        pill.pack(side="left", padx=5, pady=8)
        icon = tk.Label(pill, text="+", bg=HUD["panel"], fg=accent or HUD["cyan"], font=("Segoe UI", 11, "bold"), width=2)
        icon.pack(side="left", padx=(10, 5), pady=6)
        meta = tk.Frame(pill, bg=HUD["panel"])
        meta.pack(side="left", padx=(0, 12), pady=5)
        self._label(meta, key, fg=HUD["cyan_dim"], font=("Segoe UI", 7, "bold"), anchor="w")
        self._label(meta, textvariable=value, fg=accent or HUD["cyan"], font=("Segoe UI", 9, "bold"), anchor="w")

    def _build_content(self, main: tk.Misc) -> None:
        content = tk.Frame(main, bg=HUD["bg"])
        content.grid(row=1, column=0, sticky="nsew", padx=20, pady=18)
        content.grid_columnconfigure(0, minsize=288)
        content.grid_columnconfigure(1, weight=1)
        content.grid_columnconfigure(2, minsize=312)
        content.grid_rowconfigure(3, weight=1)

        left = tk.Frame(content, bg=HUD["bg"])
        left.grid(row=0, column=0, rowspan=3, sticky="nsew", padx=(0, 16))
        center = tk.Frame(content, bg=HUD["bg"])
        center.grid(row=0, column=1, rowspan=3, sticky="nsew", padx=(0, 16))
        right = tk.Frame(content, bg=HUD["bg"])
        right.grid(row=0, column=2, rowspan=3, sticky="nsew")

        self._build_left_column(left)
        self._build_center_column(center)
        self._build_right_column(right)
        self._build_console(content)

    def _build_left_column(self, parent: tk.Misc) -> None:
        clock = self._panel(parent, row=0, column=0, sticky="ew", pady=(0, 16))
        self._section_title(clock, "Chronometer", "HUD Online")
        self._label(clock, textvariable=self.clock_day, fg=HUD["cyan"], font=("Segoe UI", 11, "bold"), anchor="center", fill="x")
        self._label(
            clock, textvariable=self.clock_month, fg=HUD["cyan_soft"],
            font=("Segoe UI", 10), anchor="center", fill="x",
        )
        self._label(clock, textvariable=self.clock_time, fg=HUD["text"], font=("Segoe UI Light", 34), anchor="center", fill="x")
        self._label(clock, textvariable=self.clock_date, fg=HUD["cyan_dim"], font=("Segoe UI", 9), anchor="center", fill="x", pady=(0, 12))

        disk = self._panel(parent, row=1, column=0, sticky="ew", pady=(0, 16))
        self._section_title(disk, "Speicher / Disk")
        for key in ["Gesamt", "Belegt", "Frei", "Verwendung"]:
            value = "Unavailable"
            var = tk.StringVar(value=value)
            self.metric_vars[f"disk_{key}"] = var
            self._kv(disk, key, var)
        bar_wrap = tk.Frame(disk, bg=disk.cget("bg"))
        bar_wrap.pack(fill="x", padx=14, pady=(8, 14))
        self.disk_bar = tk.Canvas(bar_wrap, height=8, bg=disk.cget("bg"), highlightthickness=0)
        self.disk_bar.pack(fill="x")

        system = self._panel(parent, row=2, column=0, sticky="ew")
        self._section_title(system, "System")
        for key, value in [
            ("Uptime", "Unavailable"),
            ("CPU", "Unavailable"),
            ("RAM", "Unavailable"),
            ("Swap", "Unavailable"),
            ("Netz down", "Unavailable"),
            ("Netz up", "Unavailable"),
            ("Vault MD", "Unavailable"),
            ("Vault", "Unknown"),
            ("Inbox", "Unavailable"),
        ]:
            var = tk.StringVar(value=value)
            self.metric_vars[f"system_{key}"] = var
            self._kv(system, key, var, accent=HUD["good"] if value == "OK" else None)

    def _build_center_column(self, parent: tk.Misc) -> None:
        parent.grid_columnconfigure(0, weight=1)
        reactor_panel = tk.Frame(parent, bg=HUD["bg"])
        reactor_panel.grid(row=0, column=0, sticky="ew")
        self.reactor = tk.Canvas(reactor_panel, height=360, bg=HUD["bg"], highlightthickness=0)
        self.reactor.pack(fill="x")
        self._draw_reactor(41)

        metrics = self._panel(parent, row=1, column=0, sticky="ew", pady=(16, 16))
        self._section_title(metrics, "Live-Metriken", "Details")
        rings = tk.Frame(metrics, bg=metrics.cget("bg"))
        rings.pack(fill="x", padx=18, pady=(0, 12))
        for name, pct, color in [
            ("CPU", 0, HUD["cyan"]),
            ("RAM", 0, HUD["cyan"]),
            ("SWAP", 0, HUD["cyan"]),
            ("DISK", 0, HUD["cyan"]),
            ("QUEUE", 0, HUD["line"]),
        ]:
            self._ring(rings, name, pct, color)

        actions = self._panel(parent, row=2, column=0, sticky="ew")
        action_wrap = tk.Frame(actions, bg=actions.cget("bg"))
        action_wrap.pack(fill="x", padx=38, pady=14)
        actions_config = [
            ("V10 CYCLE", lambda: self.run_launcher(["p1-production"], title="V10 Cycle"), False),
            ("V10.1 CYCLE", lambda: self.run_launcher(["gui-doctor"], title="V10.1 Cycle"), False),
            ("IMPORT AI", lambda: self.show_view("Imports"), False),
            ("RAG INDEX", lambda: self.run_launcher(["p1-rag-status"], title="RAG Index"), False),
            ("PATH CHECK", lambda: self.run_launcher(["gui-doctor"], title="Path Check"), False),
            ("HEALTH CHECK", self.refresh_status, False),
            ("RELEASE GATE", lambda: self.run_launcher(["p1-production"], title="Release Gate"), True),
            ("REGRESSION", lambda: self.run_launcher(["gui-doctor"], title="Regression"), True),
            ("VECTOR AUDIT", lambda: self.run_launcher(["p1-vector-provider-audit"], title="Vector Audit"), False),
            ("REPAIR INDEX", self.repair_index, True),
            ("LOGS", lambda: self.show_view("Developer"), False),
            ("EINSTELLUNGEN", lambda: self.show_view("Settings"), False),
        ]
        for col in range(6):
            action_wrap.grid_columnconfigure(col, weight=1)
        for idx, (label, command, warn) in enumerate(actions_config):
            self._hud_button(action_wrap, label, command, warn=warn).grid(
                row=idx // 6,
                column=idx % 6,
                sticky="ew",
                padx=4,
                pady=4,
            )

    def _build_right_column(self, parent: tk.Misc) -> None:
        info = self._panel(parent, row=0, column=0, sticky="ew", pady=(0, 16))
        self._section_title(info, "System-Info")
        for key in ["Version", "Environment", "Database", "Embedding", "Ollama", "Memory Engine", "Queue", "Log Level"]:
            value = f"v{VERSION}" if key == "Version" else "-"
            if key == "Ollama":
                value = "Models: 0"
            if key == "Queue":
                value = "Pending: 0"
            var = tk.StringVar(value=value)
            self.info_vars[key] = var
            self._info_row(info, key, var)

        weather = self._panel(parent, row=1, column=0, sticky="ew", pady=(0, 16))
        self._section_title(weather, "Wetter", self.weather_place)
        self._label(
            weather, textvariable=self.weather_temperature, fg=HUD["text"],
            font=("Segoe UI Light", 30), side="left", padx=14, pady=(0, 12),
        )
        self._label(
            weather, textvariable=self.weather_detail, fg=HUD["cyan_dim"],
            font=("Segoe UI", 9), side="left", padx=(0, 14),
        )

        alerts = self._panel(parent, row=2, column=0, sticky="ew")
        self._section_title(alerts, "Alerts", "System")
        for key, value, color in [
            ("Release Gate", "0 Blocker", HUD["good"]),
            ("Approvals", "0 Pending", HUD["warn"]),
            ("Embedding", "Unknown", HUD["cyan"]),
            ("PostgreSQL", "Unknown", HUD["good"]),
            ("pgvector", "Not checked", HUD["cyan"]),
            ("Ollama", "Unknown", HUD["cyan"]),
            ("Backup", "Not checked", HUD["good"]),
            ("Vector Index", "Not checked", HUD["cyan"]),
            ("Queue", "0 Pending", HUD["warn"]),
        ]:
            var = tk.StringVar(value=value)
            self.alert_vars[key] = var
            label = self._kv(alerts, key, var, accent=color)
            if key == "Approvals":
                self.approval_alert_label = label

    def _build_console(self, content: tk.Misc) -> None:
        console = self._panel(content, row=3, column=0, columnspan=3, sticky="nsew", pady=(16, 0))
        self._section_title(console, "RAG / Konsole")

        cmdbar = tk.Frame(console, bg=console.cget("bg"))
        cmdbar.pack(fill="x", padx=14, pady=(0, 8))
        cmdbar.grid_columnconfigure(0, weight=1)
        self.command_entry = tk.Entry(
            cmdbar,
            bg="#00080c",
            fg=HUD["text"],
            insertbackground=HUD["text"],
            relief="flat",
            font=("Segoe UI", 11),
        )
        self.command_entry.grid(row=0, column=0, sticky="ew", ipady=7)
        self.command_entry.bind("<Return>", lambda _e: self.handle_typed_command())
        self._hud_button(cmdbar, "DEUTSCH AUSFUEHREN", self.handle_typed_command).grid(row=0, column=1, padx=(8, 0))
        self._hud_button(cmdbar, "MIKROFON 1X", self.listen_once).grid(row=0, column=2, padx=(8, 0))
        self._hud_button(cmdbar, "ABBRECHEN", self.cancel_listening, warn=True).grid(row=0, column=3, padx=(8, 0))

        self.output = tk.Text(
            console,
            bg="#00080c",
            fg=HUD["cyan_soft"],
            insertbackground=HUD["text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            padx=12,
            pady=10,
        )
        self.output.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    def _build_statusbar(self, main: tk.Misc) -> None:
        status = tk.Frame(main, bg=HUD["bg2"], highlightbackground=HUD["line2"], highlightthickness=1, bd=0)
        status.grid(row=2, column=0, sticky="ew")
        for label, value in [
            ("MODE", "NATIVE"),
            ("VOICE", "DE"),
            ("ROOT", str(self.project_root)),
            ("ACTIVE", self.current_view.get()),
        ]:
            self._label(status, f"{label}: ", fg=HUD["cyan_dim"], font=("Segoe UI", 8, "bold"), side="left", padx=(16, 0), pady=8)
            self._label(status, value, fg=HUD["text"], font=("Segoe UI", 8, "bold"), side="left", padx=(0, 12), pady=8)
        self._label(status, textvariable=self.voice_var, fg=HUD["cyan_dim"], font=("Segoe UI", 8), side="right", padx=16)

    def _info_row(self, parent: tk.Misc, key: str, var: tk.StringVar) -> None:
        row = tk.Frame(parent, bg=parent.cget("bg"))
        row.pack(fill="x", padx=14, pady=6)
        badge = tk.Label(row, text="#", bg=parent.cget("bg"), fg=HUD["cyan"], width=3)
        badge.pack(side="left", padx=(0, 8))
        text = tk.Frame(row, bg=parent.cget("bg"))
        text.pack(side="left", fill="x", expand=True)
        self._label(text, key.upper(), fg=HUD["cyan_dim"], font=("Segoe UI", 7, "bold"), anchor="w")
        self._label(text, textvariable=var, fg=HUD["text"], font=("Segoe UI", 9), anchor="w")
        tk.Frame(parent, height=1, bg=HUD["line2"]).pack(fill="x", padx=14)

    def _hud_button(self, parent: tk.Misc, text: str, command: Any, *, warn: bool = False) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            relief="flat",
            bd=0,
            padx=11,
            pady=7,
            bg="#08202b",
            fg=HUD["warn"] if warn else HUD["cyan_soft"],
            activebackground="#0d3442",
            activeforeground=HUD["text"],
            highlightbackground=HUD["warn"] if warn else HUD["line"],
            highlightthickness=1,
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
        )

    def _ring(self, parent: tk.Misc, name: str, pct: int, color: str) -> None:
        wrap = tk.Frame(parent, bg=parent.cget("bg"))
        wrap.pack(side="left", expand=True, padx=12)
        canvas = tk.Canvas(wrap, width=76, height=76, bg=parent.cget("bg"), highlightthickness=0)
        canvas.pack()
        self.metric_rings[name] = canvas
        self._draw_ring(name, pct, color)
        self._label(wrap, name, fg=HUD["cyan_dim"], font=("Segoe UI", 7, "bold"), anchor="center")

    def _draw_ring(self, name: str, pct: int, color: str, *, text: str | None = None) -> None:
        canvas = self.metric_rings.get(name)
        if canvas is None:
            return
        canvas.delete("all")
        canvas.create_oval(8, 8, 68, 68, outline="#0b3d4c", width=7)
        extent = max(0, min(100, pct)) * 3.6
        canvas.create_arc(8, 8, 68, 68, start=90, extent=-extent, outline=color, width=7, style="arc")
        canvas.create_text(38, 38, text=text or str(pct), fill=HUD["text"], font=("Segoe UI", 11, "bold"))

    def _draw_reactor(self, pct: int) -> None:
        c = self.reactor
        c.delete("all")
        width = max(600, c.winfo_width())
        cx = width // 2
        cy = 180
        for radius, color, width_line, dash in [
            (164, HUD["cyan"], 2, (12, 12)),
            (134, "#0e5262", 9, None),
            (104, HUD["cyan"], 2, (2, 14)),
            (78, "#0e5262", 4, None),
        ]:
            kwargs: dict[str, Any] = {"outline": color, "width": width_line}
            if dash:
                kwargs["dash"] = dash
            c.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, **kwargs)
        for start, extent in [(20, 45), (100, 55), (190, 52), (285, 62)]:
            c.create_arc(cx - 126, cy - 126, cx + 126, cy + 126, start=start, extent=extent, outline="#0e5262", width=12, style="arc")
        c.create_oval(cx - 70, cy - 70, cx + 70, cy + 70, fill="#06232b", outline="#0b3d4c")
        c.create_text(cx, cy - 34, text="SECONDBRAIN", fill=HUD["text"], font=("Segoe UI", 21, "bold"))
        c.create_text(cx, cy - 8, text="JARVIS CONTROL CENTER", fill=HUD["cyan"], font=("Segoe UI", 8, "bold"))
        c.create_text(cx, cy + 36, text=f"{pct}%", fill=HUD["cyan"], font=("Segoe UI Light", 34))
        c.create_text(cx, cy + 68, text="CPU LAST", fill=HUD["cyan"], font=("Segoe UI", 8, "bold"))

    def _sync_nav(self) -> None:
        active = self.current_view.get()
        for name, button in self.nav_buttons.items():
            if name == active:
                button.configure(bg=HUD["panel2"], fg=HUD["text"], highlightbackground=HUD["line"], highlightthickness=1)
            else:
                button.configure(bg=HUD["bg2"], fg=HUD["cyan_soft"], highlightthickness=0)

    def _tick_clock(self) -> None:
        now = datetime.now()
        days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        self.clock_day.set(days[now.weekday()])
        self.clock_time.set(now.strftime("%H:%M:%S"))
        self.clock_date.set(now.strftime("%d.%m.%Y"))
        self.clock_month.set(calendar_month(now))
        self.after(1000, self._tick_clock)

    def _speak_status_only(self, text: str) -> None:
        self.voice_var.set(text[:100])

    def _write(self, text: str) -> None:
        self.output.insert("end", text.rstrip() + "\n")
        self.output.see("end")

    def _json(self, payload: Any) -> None:
        self._write(json.dumps(payload, indent=2, ensure_ascii=False, default=str))

    def show_view(self, view: str) -> None:
        self.current_view.set(view)
        self._sync_nav()
        self.output.delete("1.0", "end")
        if view == "Dashboard":
            self.refresh_status()
        elif view == "Voice":
            self._json(self.voice.status())
            self._write("\nDeutsche Beispiele:\n- Jarvis Status\n- Suche PostgreSQL pgvector\n- Frage was fehlt noch\n- Oeffne Dokumente\n- Repariere Index")
        elif view == "Settings":
            self.run_launcher(["gui-bootstrap"], title="Bootstrap/Settings")
        elif view == "Production":
            self.run_launcher(["p1-production"], title="Production Gate")
        elif view == "Documents":
            self.run_launcher(["p1-rag-status"], title="Document/RAG Status")
        elif view == "Memory":
            self.run_launcher(["p3-rag-store-status"], title="Memory/RAG Store Status")
        elif view == "Search":
            self._write("Sucheingabe oben nutzen: Suche <Begriff>")
        elif view == "Imports":
            self._write("Datei per Button importieren oder Textbefehl: Importiere Datei C:\\Pfad\\datei.pdf")
        elif view == "Backups":
            self._json(self.backup_center.snapshot())
            self._write(
                "\nBackup Center / Restore Center:\n"
                "- Backup: python launcher.py ops-backup --label manuell\n"
                "- Validieren: python launcher.py ops-backup-verify <backup-id>\n"
                "- Dry Run: python launcher.py ops-restore-plan <backup-id>\n"
                "- Restore: python launcher.py ops-restore <backup-id>\n"
                "- Rollback: python launcher.py ops-restore-rollback"
            )
        elif view == "Approvals":
            self._json(self.approval_surface.snapshot())
        elif view == "Jobs":
            self._json(self.job_surface.snapshot())
        elif view == "Diagnostics":
            self._json(self._runtime_diagnostics())
        elif view == "Developer":
            self.run_launcher(["command-index"], title="Command Index")
        else:
            self._write(f"Ansicht {view}: bereit")

    def _runtime_diagnostics(self) -> dict[str, Any]:
        return runtime_diagnostics(
            voice=safe_status(self.voice.status),
            voice_state=self.action_bus.voice.state.value,
            wake=safe_status(self.wake_runtime.status),
            hotkey=safe_status(self.global_hotkey.status),
            tray_running=self.tray.running,
            approvals=safe_status(self.approval_surface.snapshot),
            jobs=safe_status(self.job_surface.snapshot),
        )

    def refresh_status(self) -> None:
        payload = write_native_status_report(self.project_root)
        ok = bool(payload.get("ok"))
        self.status_var.set("READY" if ok else "BLOCKED")
        self.info_vars.get("Version", tk.StringVar()).set(f"v{payload.get('version', VERSION)}")
        self.info_vars.get("Environment", tk.StringVar()).set(payload.get("mode", "native_desktop"))
        health = payload.get("health", {})
        self.info_vars.get("Database", tk.StringVar()).set(health.get("database", "Unknown"))
        self.info_vars.get("Embedding", tk.StringVar()).set(health.get("embedding", "Unknown"))
        self.info_vars.get("Ollama", tk.StringVar()).set(health.get("ollama", "Unknown"))
        self.info_vars.get("Memory Engine", tk.StringVar()).set(_fmt_status(payload.get("bootstrap", {}).get("ok")))
        self.info_vars.get("Log Level", tk.StringVar()).set(runtime_log_level())
        blockers = release_blocker_count(payload)
        topbar = topbar_status_labels(health, blocker_count=blockers)
        for key, value in {
            "RELEASE GATE": topbar["release_gate"],
            "EMBEDDING": topbar["embedding"],
            "POSTGRESQL": topbar["postgresql"],
        }.items():
            self.pill_vars.get(key, tk.StringVar()).set(value)
        self.alert_vars.get("Release Gate", tk.StringVar()).set("0 Blocker" if ok else f"{blockers} Blocker")
        approval_snapshot = self.approval_surface.snapshot()
        self._refresh_approval_status(snapshot=approval_snapshot, schedule=False)
        jobs = self.job_surface.snapshot()
        alerts = live_alert_labels(health=health, jobs=jobs)
        for key, value in {
            "Embedding": alerts["embedding"],
            "PostgreSQL": alerts["postgresql"],
            "pgvector": alerts["pgvector"],
            "Ollama": alerts["ollama"],
        }.items():
            self.alert_vars.get(key, tk.StringVar()).set(value)
        self._refresh_queue_status(jobs=jobs, schedule=False)
        storage_alerts = storage_alert_labels(
            backup=safe_status(self.backup_center.snapshot),
            vector=read_vector_validation(self.project_root),
        )
        self.alert_vars.get("Backup", tk.StringVar()).set(storage_alerts["backup"])
        self.alert_vars.get("Vector Index", tk.StringVar()).set(storage_alerts["vector_index"])
        vault = vault_status_labels(safe_status(self.live_data.dashboard))
        self.metric_vars.get("system_Vault MD", tk.StringVar()).set(vault["markdown"])
        self.metric_vars.get("system_Vault", tk.StringVar()).set(vault["vault"])
        self.metric_vars.get("system_Inbox", tk.StringVar()).set(vault["inbox"])
        self._refresh_system_metrics(schedule=False)
        self.output.delete("1.0", "end")
        self._write(bootstrap_text(self.project_root, repair=True))
        self._write("\nNative Status:")
        self._json(payload)

    def _refresh_approval_status(
        self, *, snapshot: dict[str, Any] | None = None, schedule: bool = True
    ) -> None:
        current = snapshot if snapshot is not None else safe_status(self.approval_surface.snapshot)
        activity = approval_activity(dict(current))
        self.alert_vars.get("Approvals", tk.StringVar()).set(activity["label"])
        self.approval_tray_status = activity["label"]
        if activity["available"]:
            notification = approval_notification(self.approval_pending_count, activity["pending"])
            self.approval_pending_count = activity["pending"]
            if notification is not None:
                self.tray.notify(notification)
        if self.approval_alert_label is not None:
            color = {
                "critical": HUD["bad"],
                "warning": HUD["warn"],
                "normal": HUD["good"],
                "unavailable": HUD["bad"],
            }[activity["severity"]]
            self.approval_alert_label.configure(fg=color)
        if schedule:
            self.after(2000, self._refresh_approval_status)

    def _refresh_queue_status(self, *, jobs: dict[str, Any] | None = None, schedule: bool = True) -> None:
        snapshot = jobs if jobs is not None else safe_status(self.job_surface.snapshot)
        activity = queue_activity(snapshot)
        self.info_vars.get("Queue", tk.StringVar()).set(
            f"Running: {activity['running']} / Active: {activity['active']}"
        )
        self.alert_vars.get("Queue", tk.StringVar()).set(activity["alert"])
        active = int(activity["active"])
        color = HUD["warn"] if activity["blocked"] or active else HUD["line"]
        self._draw_ring("QUEUE", 100 if active else 0, color, text=str(active))
        if schedule:
            self.after(2000, self._refresh_queue_status)

    def _refresh_system_metrics(self, *, schedule: bool = True) -> None:
        metrics = self.system_metrics_sampler.read(self.project_root)
        self.system_metrics = metrics
        values = metrics if metrics.get("available") else {}
        labels = {
            "disk_Gesamt": format_bytes(values.get("disk_total")),
            "disk_Belegt": format_bytes(values.get("disk_used")),
            "disk_Frei": format_bytes(values.get("disk_free")),
            "disk_Verwendung": format_percent(values.get("disk_percent")),
            "system_Uptime": format_uptime(values.get("uptime_seconds")),
            "system_CPU": format_percent(values.get("cpu_percent")),
            "system_RAM": format_percent(values.get("ram_percent")),
            "system_Swap": format_percent(values.get("swap_percent")),
            "system_Netz down": format_kbps(
                values.get("net_down_kbps") if values.get("network_available") else None
            ),
            "system_Netz up": format_kbps(
                values.get("net_up_kbps") if values.get("network_available") else None
            ),
        }
        for key, value in labels.items():
            if key in self.metric_vars:
                self.metric_vars[key].set(value)
        for name, key in [("CPU", "cpu_percent"), ("RAM", "ram_percent"), ("SWAP", "swap_percent"), ("DISK", "disk_percent")]:
            pct = int(float(values.get(key, 0)))
            color = HUD["warn"] if pct >= 80 else HUD["cyan"]
            self._draw_ring(name, pct, color)
        cpu = int(float(values.get("cpu_percent", 0)))
        self.after_idle(lambda: self._draw_reactor(cpu))
        self.after_idle(self._draw_disk_bar)
        if schedule:
            self.after(5000, self._refresh_system_metrics)

    def _draw_disk_bar(self) -> None:
        self.disk_bar.delete("all")
        width = max(10, self.disk_bar.winfo_width())
        self.disk_bar.create_rectangle(0, 0, width, 8, fill="#08202b", outline=HUD["line"])
        pct = float(self.system_metrics.get("disk_percent", 0))
        self.disk_bar.create_rectangle(0, 0, int(width * pct / 100), 8, fill=HUD["cyan"], outline="")

    def run_launcher(self, args: list[str], *, title: str | None = None) -> None:
        self.status_var.set("laeuft")
        if title:
            self._write(f"\n## {title}\n$ python launcher.py {' '.join(args)}")

        def worker() -> None:
            try:
                proc = subprocess.run(
                    [sys.executable, "launcher.py"] + args,
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=120,
                )
                self.queue.put(("launcher", {"args": args, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}))
            except Exception as exc:
                self.queue.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _drain_queue(self) -> None:
        while True:
            try:
                kind, payload = self.queue.get_nowait()
            except queue.Empty:
                break
            if kind == "voice":
                capture_status = payload.get("status")
                if not payload.get("ok") and capture_status not in {"busy", "cancelled"}:
                    self.action_bus.voice.set_audio_state("ERROR")
                self.status_var.set("READY" if payload.get("ok") or capture_status in {"busy", "cancelled"} else "STT FEHLER")
                self._json(payload)
                if payload.get("ok") and payload.get("text"):
                    self._submit_action(payload["text"])
            elif kind == "action_bus":
                self._handle_action_result(payload)
            elif kind == "launcher":
                self.status_var.set("READY" if payload["returncode"] == 0 else "BLOCKED")
                if payload["stdout"]:
                    self._write(payload["stdout"])
                if payload["stderr"]:
                    self._write("STDERR:\n" + payload["stderr"])
            elif kind == "weather":
                labels = weather_labels(payload)
                self.weather_place.set(labels["place"])
                self.weather_temperature.set(labels["temperature"])
                self.weather_detail.set(labels["detail"])
            else:
                self.status_var.set("FEHLER")
                self._write(str(payload))
        self.after(200, self._drain_queue)

    def _request_weather(self) -> None:
        config = weather_config()

        def worker() -> None:
            self.queue.put(("weather", fetch_weather(config)))

        threading.Thread(target=worker, daemon=True).start()
        self.after(15 * 60 * 1000, self._request_weather)

    def handle_typed_command(self) -> None:
        text = self.command_entry.get().strip()
        self.command_entry.delete(0, "end")
        if not text:
            return
        self._write(f"\n> {text}")
        self._submit_action(text)

    def _submit_action(self, text: str) -> None:
        self.status_var.set("VERARBEITET")

        def worker() -> None:
            self.queue.put(("action_bus", self.action_bus.submit(text)))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_action_result(self, result: dict[str, Any]) -> None:
        self.status_var.set("READY" if result.get("status") != "error" else "FEHLER")
        prompt = dialog_prompt(result)
        if prompt:
            self.voice_var.set(prompt)
            self._write(f"\nJarvis: {prompt}")
            if self.dialog_tts_enabled:
                threading.Thread(target=lambda: self.voice.speak(prompt), daemon=True).start()
        payload = result.get("result") or {}
        next_view = payload.get("next_view") if isinstance(payload, dict) else None
        if next_view:
            self.show_view(display_view(next_view))
        self._json(result)

    def listen_once(self) -> None:
        self.status_var.set("hoert zu")

        def worker() -> None:
            result = self.voice.listen_once()
            self.queue.put(("voice", result))

        threading.Thread(target=worker, daemon=True).start()

    def cancel_listening(self) -> None:
        if self.voice.cancel_listening():
            self.action_bus.voice.set_audio_state("IDLE")
            self.voice_var.set("Sprachaufnahme abgebrochen")

    def execute_voice_command(self, command: dict[str, Any]) -> None:
        intent = command.get("intent")
        args = command.get("args") or {}
        if intent == "status":
            self.show_view("Dashboard")
        elif intent == "production_gate":
            self.show_view("Production")
        elif intent == "open_view":
            mapping = {"documents": "Documents", "memory": "Memory", "settings": "Settings"}
            self.show_view(mapping.get(args.get("view"), "Dashboard"))
        elif intent == "rag_search":
            query = args.get("query", "")
            self.run_launcher(["p1-rag-hybrid-search", query], title="RAG Suche")
        elif intent == "rag_answer":
            query = args.get("query", "")
            self.run_launcher(["p1-rag-answer", query], title="RAG Antwort")
        elif intent == "ingest_file":
            path = args.get("path", "")
            if path and messagebox.askyesno("Import bestaetigen", f"Datei importieren?\n{path}"):
                self.run_launcher(["p1-rag-ingest-file", path], title="Dateiimport")
        elif intent == "vector_repair":
            if messagebox.askyesno("Index reparieren", "Vector Index wirklich reparieren/reindizieren?"):
                self.run_launcher(["p1-vector-index-repair", "--write-report"], title="Vector Index Repair")
        elif intent == "stop_listening":
            self.voice_var.set("Sprachsteuerung pausiert")
        else:
            self._write("Kein direkter Tool-Befehl. Nutze Suche/Frage/Status/Oeffne Dokumente/Repariere Index.")

    def import_file(self) -> None:
        path = filedialog.askopenfilename(title="Datei ins SecondBrain importieren")
        if path:
            self.run_launcher(["p1-rag-ingest-file", path], title="Dateiimport")

    def repair_index(self) -> None:
        if messagebox.askyesno("Index reparieren", "Vector Index reparieren/reindizieren?"):
            self.run_launcher(["p1-vector-index-repair", "--write-report"], title="Vector Index Repair")


def main(project_root: str | Path | None = None) -> int:
    root = Path(project_root or Path.cwd()).resolve()
    try:
        with SingleInstanceLock(root):
            app = JarvisNativeApp(root)
            app.mainloop()
            return 0
    except InstanceAlreadyRunning as exc:
        print(str(exc), file=sys.stderr)
        return 3
