from __future__ import annotations

from pathlib import Path
from tkinter import BOTH, END, LEFT, RIGHT, Button, Frame, Label, Listbox, Tk, Text
from typing import Any

from .service import ThemeCenterService


def run_gui(project_root: str | Path = ".") -> dict[str, Any]:
    svc = ThemeCenterService(project_root)
    root = Tk()
    root.title("Jarvis Theme Center")
    root.geometry("920x560")

    status = svc.status()
    current = status.get("current", {})
    tokens = current.get("tokens", {})
    root.configure(bg=tokens.get("background", "#0b1220"))

    sidebar = Frame(root, bg=tokens.get("surface", "#111827"), width=260)
    sidebar.pack(side=LEFT, fill="y")
    content = Frame(root, bg=tokens.get("background", "#0b1220"))
    content.pack(side=RIGHT, fill=BOTH, expand=True)

    title = Label(sidebar, text="Themes", bg=tokens.get("surface", "#111827"), fg=tokens.get("text", "#e5e7eb"), font=("Segoe UI", 14, "bold"))
    title.pack(pady=12)

    theme_list = Listbox(sidebar, bg=tokens.get("surface_raised", "#172033"), fg=tokens.get("text", "#e5e7eb"), selectbackground=tokens.get("accent", "#38bdf8"))
    theme_list.pack(fill=BOTH, expand=True, padx=10, pady=10)
    themes = svc.themes()
    for theme in themes:
        marker = "* " if theme.id == svc.current_theme_id() else "  "
        theme_list.insert(END, f"{marker}{theme.name} [{theme.id}]")

    detail = Text(content, bg=tokens.get("surface", "#111827"), fg=tokens.get("text", "#e5e7eb"), insertbackground=tokens.get("text", "#e5e7eb"))
    detail.pack(fill=BOTH, expand=True, padx=12, pady=12)

    def selected_theme_id() -> str:
        selection = theme_list.curselection()
        if not selection:
            return svc.current_theme_id()
        return themes[int(selection[0])].id

    def refresh_detail() -> None:
        preview = svc.preview(selected_theme_id())
        detail.delete("1.0", END)
        if preview.get("ok"):
            theme = preview["theme"]
            detail.insert(END, f"{theme['name']}\n")
            detail.insert(END, f"ID: {theme['id']}\n")
            detail.insert(END, f"Modus: {theme['mode']}\n")
            detail.insert(END, f"Dichte: {theme['density']}\n\n")
            detail.insert(END, f"{theme['description']}\n\n")
            for key, value in theme["tokens"].items():
                detail.insert(END, f"{key}: {value}\n")
        else:
            detail.insert(END, str(preview))

    def activate_selected() -> None:
        svc.activate(selected_theme_id())
        detail.insert(END, "\nTheme aktiviert. Fenster neu öffnen, damit alle Flächen neu gezeichnet werden.\n")

    controls = Frame(content, bg=tokens.get("background", "#0b1220"))
    controls.pack(fill="x", padx=12, pady=(0, 12))
    Button(controls, text="Vorschau", command=refresh_detail).pack(side=LEFT, padx=4)
    Button(controls, text="Aktivieren", command=activate_selected).pack(side=LEFT, padx=4)
    Button(controls, text="Zurücksetzen", command=lambda: [svc.reset(), refresh_detail()]).pack(side=LEFT, padx=4)

    theme_list.bind("<<ListboxSelect>>", lambda _event: refresh_detail())
    refresh_detail()
    root.mainloop()
    return {"ok": True, "gui": "theme_center"}
