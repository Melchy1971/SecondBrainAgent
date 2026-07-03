"""Embedded v30.48 project/workspace panel for the existing AI Workspace."""
from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, simpledialog, ttk

from .project_workspace import ProjectWorkspaceService


class ProjectWorkspaceFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, project_root: str | Path):
        super().__init__(master)
        self.service = ProjectWorkspaceService(project_root)
        self.query = tk.StringVar()
        self.view = tk.StringVar(value="active")
        self.message = tk.StringVar()
        self._build()
        self.reload()

    def _build(self) -> None:
        filters = ttk.Frame(self, padding=6); filters.pack(fill="x")
        ttk.Entry(filters, textvariable=self.query).pack(side="left", fill="x", expand=True)
        ttk.Combobox(filters, textvariable=self.view, values=("active", "favorites", "archive", "trash", "all"), state="readonly", width=12).pack(side="left", padx=4)
        ttk.Button(filters, text="Suchen", command=self.reload).pack(side="left")
        ttk.Button(filters, text="Import", command=self.import_data).pack(side="left", padx=(12, 2))
        ttk.Button(filters, text="Export", command=self.export_data).pack(side="left")
        self.tabs = ttk.Notebook(self); self.tabs.pack(fill="both", expand=True)
        projects = ttk.Frame(self.tabs); workspaces = ttk.Frame(self.tabs); access = ttk.Frame(self.tabs)
        self.tabs.add(projects, text="Projekte"); self.tabs.add(workspaces, text="Workspaces"); self.tabs.add(access, text="Benutzer / Rollen")
        self.project_tree = ttk.Treeview(projects, columns=("workspace", "tags", "favorite", "state"), show="tree headings")
        for column, title in (("#0", "Projekt"), ("workspace", "Workspace"), ("tags", "Tags"), ("favorite", "Favorit"), ("state", "Status")):
            self.project_tree.heading(column, text=title)
        self.project_tree.pack(fill="both", expand=True)
        actions = ttk.Frame(projects); actions.pack(fill="x", pady=4)
        for title, command in (("Neu", self.add_project), ("Favorit", self.favorite), ("Tags", self.edit_tags),
                               ("Archiv", self.archive), ("Papierkorb", self.trash), ("Wiederherstellen", self.restore)):
            ttk.Button(actions, text=title, command=command).pack(side="left", padx=2)
        self.workspace_tree = ttk.Treeview(workspaces, columns=("root", "active"), show="tree headings")
        self.workspace_tree.heading("#0", text="Workspace"); self.workspace_tree.heading("root", text="Pfad"); self.workspace_tree.heading("active", text="Aktiv")
        self.workspace_tree.pack(fill="both", expand=True)
        workspace_actions = ttk.Frame(workspaces); workspace_actions.pack(fill="x", pady=4)
        ttk.Button(workspace_actions, text="Neu", command=self.add_workspace).pack(side="left")
        ttk.Button(workspace_actions, text="Aktivieren", command=self.switch_workspace).pack(side="left", padx=4)
        self.user_tree = ttk.Treeview(access, columns=("role", "permissions"), show="tree headings")
        self.user_tree.heading("#0", text="Benutzer"); self.user_tree.heading("role", text="Rolle"); self.user_tree.heading("permissions", text="Rechte")
        self.user_tree.pack(fill="both", expand=True)
        ttk.Button(access, text="Benutzer hinzufuegen", command=self.add_user).pack(anchor="w", pady=4)
        ttk.Label(self, textvariable=self.message).pack(fill="x")

    def reload(self) -> None:
        payload = self.service.snapshot(view=self.view.get(), query=self.query.get())
        for tree in (self.project_tree, self.workspace_tree, self.user_tree):
            for item in tree.get_children(): tree.delete(item)
        for row in payload["projects"]:
            self.project_tree.insert("", "end", iid=row["id"], text=row["name"], values=(row["workspace_id"], ", ".join(row["tags"]), "ja" if row["favorite"] else "", row["state"]))
        for row in payload["workspaces"]:
            self.workspace_tree.insert("", "end", iid=row["workspace_id"], text=row["name"], values=(row["root_path"], "ja" if row["active"] else ""))
        for row in payload["access"]["users"]:
            self.user_tree.insert("", "end", iid=row["id"], text=row["display_name"], values=(row["role"], ", ".join(row["permissions"])))
        self.message.set(f"{payload['summary']['projects']} Projekte | {payload['summary']['workspaces']} Workspaces")

    def _selected(self, tree):
        selected = tree.selection()
        return selected[0] if selected else None

    def add_project(self):
        name = simpledialog.askstring("Projekt", "Name", parent=self)
        if name: self.service.add_project(name); self.reload()

    def favorite(self):
        project_id = self._selected(self.project_tree)
        if project_id: self.service.set_favorite(project_id, self.service.normalize(next(row for row in self.service.projects(view="all") if row["id"] == project_id))["favorite"] is False); self.reload()

    def edit_tags(self):
        project_id = self._selected(self.project_tree)
        if project_id:
            value = simpledialog.askstring("Tags", "Kommagetrennte Tags", parent=self)
            if value is not None: self.service.set_tags(project_id, value.split(",")); self.reload()

    def archive(self): self._lifecycle(self.service.archive)
    def trash(self): self._lifecycle(self.service.trash)
    def restore(self): self._lifecycle(self.service.restore)

    def _lifecycle(self, action):
        project_id = self._selected(self.project_tree)
        if project_id: action(project_id); self.reload()

    def add_workspace(self):
        name = simpledialog.askstring("Workspace", "Name", parent=self)
        if not name: return
        root = filedialog.askdirectory(parent=self)
        if root: self.service.create_workspace(name.lower().replace(" ", "-"), name, root); self.reload()

    def switch_workspace(self):
        workspace_id = self._selected(self.workspace_tree)
        if workspace_id: self.service.switch_workspace(workspace_id); self.reload()

    def add_user(self):
        user_id = simpledialog.askstring("Benutzer", "Benutzer-ID", parent=self)
        if user_id: self.service.add_user(user_id); self.reload()

    def import_data(self):
        path = filedialog.askopenfilename(parent=self, filetypes=[("JSON", "*.json")])
        if path: self.service.import_data(path); self.reload()

    def export_data(self):
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path: self.service.export_data(path); self.message.set(f"Export: {path}")
