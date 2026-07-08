from __future__ import annotations

import json
from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, TOP, Button, Frame, Label, Listbox, Text, Tk, messagebox

from .command_center import CommandCenter


class CommandCenterWindow:
    def __init__(self, project_root: str | Path = ".") -> None:
        self.center = CommandCenter(project_root)
        self.root = Tk()
        self.root.title("Jarvis Command Center")
        self.root.geometry("980x680")
        self.commands = self.center.catalog()
        self._build()

    def _build(self) -> None:
        header = Frame(self.root)
        header.pack(side=TOP, fill="x")
        Label(header, text="Jarvis Command Center", font=("Segoe UI", 16, "bold")).pack(side=LEFT, padx=10, pady=8)
        Button(header, text="Status", command=self._status).pack(side=RIGHT, padx=8)

        body = Frame(self.root)
        body.pack(fill=BOTH, expand=True)
        self.listbox = Listbox(body, width=42)
        self.listbox.pack(side=LEFT, fill="y", padx=8, pady=8)
        for command in self.commands:
            marker = "!" if command.get("requires_confirmation") else " "
            self.listbox.insert(END, f"{marker} {command['title']} [{command['category']}]")

        right = Frame(body)
        right.pack(side=RIGHT, fill=BOTH, expand=True, padx=8, pady=8)
        buttons = Frame(right)
        buttons.pack(side=TOP, fill="x")
        Button(buttons, text="Trockenlauf", command=lambda: self._run(True)).pack(side=LEFT, padx=4)
        Button(buttons, text="Ausführen", command=lambda: self._run(False)).pack(side=LEFT, padx=4)
        Button(buttons, text="Freigaben", command=self._approvals).pack(side=LEFT, padx=4)
        Button(buttons, text="Verlauf", command=self._history).pack(side=LEFT, padx=4)

        self.output = Text(right, wrap="word")
        self.output.pack(fill=BOTH, expand=True, pady=8)
        self._status()

    def _selected_id(self) -> str | None:
        selection = self.listbox.curselection()
        if not selection:
            return None
        return self.commands[selection[0]]["id"]

    def _write(self, payload: object) -> None:
        self.output.delete("1.0", END)
        self.output.insert(END, json.dumps(payload, indent=2, ensure_ascii=False, default=str))

    def _status(self) -> None:
        self._write(self.center.status())

    def _run(self, dry_run: bool) -> None:
        command_id = self._selected_id()
        if not command_id:
            messagebox.showwarning("Jarvis", "Kein Befehl ausgewählt.")
            return
        payload = self.center.run(command_id, dry_run=dry_run)
        self._write(payload)

    def _approvals(self) -> None:
        self._write({"pending_approvals": self.center.pending_approvals()})

    def _history(self) -> None:
        self._write({"history": self.center.history(25)})

    def run(self) -> int:
        self.root.mainloop()
        return 0


def run_command_center_gui(project_root: str | Path = ".") -> int:
    return CommandCenterWindow(project_root).run()
