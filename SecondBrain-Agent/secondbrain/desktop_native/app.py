from __future__ import annotations

import json
import queue
import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from secondbrain.desktop_native.status import write_native_status_report
from secondbrain.desktop_native.voice_de import GermanVoiceController, parse_german_voice_command
from secondbrain.gui.bootstrap import bootstrap_text, write_bootstrap_report

VERSION = "30.25"
TITLE = "Jarvis SecondBrain - Native Desktop"

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

NAV_ITEMS = [
    "Dashboard",
    "Assistant",
    "Documents",
    "Memory",
    "Knowledge",
    "Search",
    "Imports",
    "Jobs",
    "Connectors",
    "Agents",
    "Settings",
    "Developer",
]


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
        self.voice = GermanVoiceController(self.project_root, speaker=self._speak_status_only)
        self.queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.current_view = tk.StringVar(value="Dashboard")
        self.status_var = tk.StringVar(value="Initialisiere")
        self.voice_var = tk.StringVar(value="Deutsch - bereit fuer Textbefehle")
        self.clock_time = tk.StringVar(value="")
        self.clock_day = tk.StringVar(value="")
        self.clock_date = tk.StringVar(value="")
        self.metric_vars: dict[str, tk.StringVar] = {}
        self.info_vars: dict[str, tk.StringVar] = {}
        self.alert_vars: dict[str, tk.StringVar] = {}
        self.nav_buttons: dict[str, tk.Button] = {}
        self.geometry("1500x900")
        self.minsize(1180, 720)
        self.title(TITLE)
        self.configure(bg=HUD["bg"])
        self._configure_theme()
        self._build_layout()
        self.after(100, self.refresh_status)
        self.after(200, self._drain_queue)
        self._tick_clock()

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

    def _section_title(self, parent: tk.Misc, title: str, meta: str = "") -> None:
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
            self._label(
                bar,
                meta.upper(),
                fg=HUD["cyan_dim"],
                font=("Segoe UI", 8, "bold"),
                side="right",
            )
        tk.Frame(bar, height=1, bg=HUD["line2"]).pack(fill="x", side="bottom", pady=(8, 0))

    def _kv(self, parent: tk.Misc, key: str, var: tk.StringVar, *, accent: str | None = None) -> None:
        row = tk.Frame(parent, bg=parent.cget("bg"))
        row.pack(fill="x", padx=14, pady=3)
        self._label(row, key, fg=HUD["cyan_soft"], font=("Segoe UI", 9, "bold"), side="left")
        self._label(row, textvariable=var, fg=accent or HUD["text"], font=("Segoe UI", 9, "bold"), side="right")
        tk.Frame(parent, height=1, bg=HUD["line2"]).pack(fill="x", padx=14)

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
        self._hud_button(quick, "REPAIR INDEX", self.repair_index, warn=True).pack(fill="x", pady=3)

    def _build_topbar(self, main: tk.Misc) -> None:
        top = tk.Frame(main, bg=HUD["bg2"], highlightbackground=HUD["line2"], highlightthickness=1, bd=0)
        top.grid(row=0, column=0, sticky="ew")
        title = tk.Frame(top, bg=HUD["bg2"])
        title.pack(side="left", padx=20, pady=9)
        self._label(title, "SECONDBRAIN", fg=HUD["text"], font=("Segoe UI", 18, "bold"), anchor="w")
        self._label(title, f"JARVIS CONTROL CENTER   v{VERSION}", fg=HUD["cyan"], font=("Segoe UI", 8, "bold"), anchor="w")

        self._pill(top, "SYSTEM HEALTH", self.status_var, accent=HUD["good"])
        self._pill(top, "RELEASE GATE", tk.StringVar(value="BLOCKING 0"), accent=HUD["good"])
        self._pill(top, "EMBEDDING", tk.StringVar(value="-"))
        self._pill(top, "POSTGRESQL", tk.StringVar(value="-"))

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
        self._label(clock, "Juni 26", fg=HUD["cyan_soft"], font=("Segoe UI", 10), anchor="center", fill="x")
        self._label(clock, textvariable=self.clock_time, fg=HUD["text"], font=("Segoe UI Light", 34), anchor="center", fill="x")
        self._label(clock, textvariable=self.clock_date, fg=HUD["cyan_dim"], font=("Segoe UI", 9), anchor="center", fill="x", pady=(0, 12))

        disk = self._panel(parent, row=1, column=0, sticky="ew", pady=(0, 16))
        self._section_title(disk, "Speicher / Disk")
        for key, value in [("Gesamt", "34.3 GB"), ("Belegt", "26.3 GB"), ("Frei", "8 GB"), ("Verwendung", "77%")]:
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
            ("Uptime", "1d 12h 52min"),
            ("CPU", "41%"),
            ("RAM", "88%"),
            ("Swap", "17%"),
            ("Netz down", "356.4 KB/s"),
            ("Netz up", "8.4 KB/s"),
            ("Vault MD", "392"),
            ("Vault", "OK"),
            ("Inbox", "OK"),
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
            ("CPU", 41, HUD["cyan"]),
            ("RAM", 88, HUD["warn"]),
            ("SWAP", 17, HUD["cyan"]),
            ("DISK", 77, HUD["warn"]),
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
            value = "v30.25" if key == "Version" else "-"
            if key == "Ollama":
                value = "Models: 0"
            if key == "Queue":
                value = "Pending: 0"
            var = tk.StringVar(value=value)
            self.info_vars[key] = var
            self._info_row(info, key, var)

        weather = self._panel(parent, row=1, column=0, sticky="ew", pady=(0, 16))
        self._section_title(weather, "Wetter", "Zaberfeld")
        self._label(weather, "34 deg", fg=HUD["text"], font=("Segoe UI Light", 30), side="left", padx=14, pady=(0, 12))
        self._label(weather, "Heiter\nFeuchte 39%\nWind 11 km/h", fg=HUD["cyan_dim"], font=("Segoe UI", 9), side="left", padx=(0, 14))

        alerts = self._panel(parent, row=2, column=0, sticky="ew")
        self._section_title(alerts, "Alerts", "System")
        for key, value, color in [
            ("Release Gate", "0 Blocker", HUD["good"]),
            ("Embedding", "-", HUD["cyan"]),
            ("PostgreSQL", "-", HUD["good"]),
            ("pgvector", "-", HUD["cyan"]),
            ("Ollama", "0 Models", HUD["cyan"]),
            ("Backup", "Letztes: -", HUD["good"]),
            ("Vector Index", "-", HUD["cyan"]),
            ("Queue", "0 Pending", HUD["warn"]),
        ]:
            var = tk.StringVar(value=value)
            self.alert_vars[key] = var
            self._kv(alerts, key, var, accent=color)

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
        canvas.create_oval(8, 8, 68, 68, outline="#0b3d4c", width=7)
        extent = max(0, min(100, pct)) * 3.6
        canvas.create_arc(8, 8, 68, 68, start=90, extent=-extent, outline=color, width=7, style="arc")
        canvas.create_text(38, 38, text=str(pct), fill=HUD["text"], font=("Segoe UI", 11, "bold"))
        self._label(wrap, name, fg=HUD["cyan_dim"], font=("Segoe UI", 7, "bold"), anchor="center")

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
        elif view == "Developer":
            self.run_launcher(["command-index"], title="Command Index")
        else:
            self._write(f"Ansicht {view}: bereit")

    def refresh_status(self) -> None:
        payload = write_native_status_report(self.project_root)
        ok = bool(payload.get("ok"))
        self.status_var.set("READY" if ok else "BLOCKED")
        self.info_vars.get("Version", tk.StringVar()).set(f"v{payload.get('version', VERSION)}")
        self.info_vars.get("Environment", tk.StringVar()).set(payload.get("mode", "native_desktop"))
        self.info_vars.get("Database", tk.StringVar()).set("local")
        self.info_vars.get("Embedding", tk.StringVar()).set("-")
        self.info_vars.get("Memory Engine", tk.StringVar()).set(_fmt_status(payload.get("bootstrap", {}).get("ok")))
        self.alert_vars.get("Release Gate", tk.StringVar()).set("0 Blocker" if ok else f"{len(payload.get('blockers', []))} Blocker")
        self.output.delete("1.0", "end")
        self._write(bootstrap_text(self.project_root, repair=True))
        self._write("\nNative Status:")
        self._json(payload)
        self.after_idle(lambda: self._draw_reactor(41))
        self.after_idle(self._draw_disk_bar)

    def _draw_disk_bar(self) -> None:
        self.disk_bar.delete("all")
        width = max(10, self.disk_bar.winfo_width())
        self.disk_bar.create_rectangle(0, 0, width, 8, fill="#08202b", outline=HUD["line"])
        self.disk_bar.create_rectangle(0, 0, int(width * 0.77), 8, fill=HUD["cyan"], outline="")

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
                self.status_var.set("READY" if payload.get("ok") else "STT FEHLER")
                self._json(payload)
                if payload.get("ok") and payload.get("command"):
                    self.execute_voice_command(payload["command"])
            elif kind == "launcher":
                self.status_var.set("READY" if payload["returncode"] == 0 else "BLOCKED")
                if payload["stdout"]:
                    self._write(payload["stdout"])
                if payload["stderr"]:
                    self._write("STDERR:\n" + payload["stderr"])
            else:
                self.status_var.set("FEHLER")
                self._write(str(payload))
        self.after(200, self._drain_queue)

    def handle_typed_command(self) -> None:
        text = self.command_entry.get().strip()
        self.command_entry.delete(0, "end")
        if not text:
            return
        command = parse_german_voice_command(text)
        self._write(f"\n> {text}\nIntent: {command.intent}")
        self.execute_voice_command(command.to_dict())

    def listen_once(self) -> None:
        self.status_var.set("hoert zu")

        def worker() -> None:
            result = self.voice.listen_once()
            self.queue.put(("voice", result))

        threading.Thread(target=worker, daemon=True).start()

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
    app = JarvisNativeApp(project_root)
    app.mainloop()
    return 0
