"""Embedded canvas-based Semantic Explorer for the AI Workspace."""
from __future__ import annotations

import json
import math
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from .semantic_explorer import SemanticExplorerService, VIEW_TYPES


class SemanticExplorerFrame(ttk.Frame):
    COLORS = {"document": "#60A5FA", "memory": "#A78BFA", "person": "#F59E0B", "project": "#34D399",
              "workspace": "#22D3EE", "tag": "#F472B6", "source": "#94A3B8", "concept": "#E5E7EB"}

    def __init__(self, master: tk.Misc, project_root: str | Path):
        super().__init__(master)
        self.service = SemanticExplorerService(project_root)
        self.query = tk.StringVar()
        self.view = tk.StringVar(value="knowledge")
        self.node_type = tk.StringVar()
        self.relationship_type = tk.StringVar()
        self.source = tk.StringVar()
        self.tag = tk.StringVar()
        self.status = tk.StringVar()
        self.navigation: list[str] = []
        self._build()
        self.reload()

    def _build(self) -> None:
        bar = ttk.Frame(self, padding=6); bar.pack(fill="x")
        ttk.Entry(bar, textvariable=self.query).pack(side="left", fill="x", expand=True)
        ttk.Combobox(bar, textvariable=self.view, values=tuple(VIEW_TYPES), state="readonly", width=15).pack(side="left", padx=3)
        self.node_filter = ttk.Combobox(bar, textvariable=self.node_type, state="readonly", width=13)
        self.node_filter.pack(side="left", padx=3)
        self.relationship_filter = ttk.Combobox(bar, textvariable=self.relationship_type, state="readonly", width=18)
        self.relationship_filter.pack(side="left", padx=3)
        self.source_filter = ttk.Combobox(bar, textvariable=self.source, state="readonly", width=14)
        self.source_filter.pack(side="left", padx=3)
        self.tag_filter = ttk.Combobox(bar, textvariable=self.tag, state="readonly", width=12)
        self.tag_filter.pack(side="left", padx=3)
        ttk.Button(bar, text="Suchen", command=self.reload).pack(side="left")
        ttk.Button(bar, text="Zurueck", command=self.back).pack(side="left", padx=3)
        body = ttk.PanedWindow(self, orient="horizontal"); body.pack(fill="both", expand=True)
        graph_frame, side = ttk.Frame(body), ttk.Frame(body, padding=4)
        body.add(graph_frame, weight=4); body.add(side, weight=1)
        self.canvas = tk.Canvas(graph_frame, background="#0F172A", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self._draw(self.current) if hasattr(self, "current") else None)
        self.nodes = ttk.Treeview(side, columns=("type", "source"), show="tree headings")
        self.nodes.heading("#0", text="Knoten"); self.nodes.heading("type", text="Typ"); self.nodes.heading("source", text="Quelle")
        self.nodes.pack(fill="both", expand=True); self.nodes.bind("<<TreeviewSelect>>", self._tree_select)
        self.details = tk.Text(side, height=12, wrap="word", state="disabled"); self.details.pack(fill="x", pady=(4, 0))
        ttk.Label(self, textvariable=self.status).pack(fill="x")

    def reload(self) -> None:
        self.current = self.service.explore(view=self.view.get(), query=self.query.get(),
            node_types=[self.node_type.get()] if self.node_type.get() else [],
            relationship_types=[self.relationship_type.get()] if self.relationship_type.get() else [],
            sources=[self.source.get()] if self.source.get() else [], tags=[self.tag.get()] if self.tag.get() else [])
        available = self.current["available"]
        self.node_filter.configure(values=("", *available["node_types"]))
        self.relationship_filter.configure(values=("", *available["relationship_types"]))
        self.source_filter.configure(values=("", *available["sources"]))
        self.tag_filter.configure(values=("", *available["tags"]))
        self._render(self.current)

    def _render(self, payload) -> None:
        for item in self.nodes.get_children(): self.nodes.delete(item)
        for row in payload["nodes"]:
            self.nodes.insert("", "end", iid=row["id"], text=row["label"], values=(row["type"], ", ".join(row["sources"][:2])))
        self._draw(payload)
        self.status.set(f"{len(payload['nodes'])} Knoten | {len(payload['edges'])} Beziehungen | read-only RAG/Memory")

    def _draw(self, payload) -> None:
        self.canvas.delete("all")
        nodes = payload.get("nodes", [])[:80]
        if not nodes: return
        width, height = max(self.canvas.winfo_width(), 600), max(self.canvas.winfo_height(), 400)
        radius = max(80, min(width, height) / 2 - 60); center = (width / 2, height / 2)
        positions = {row["id"]: (center[0] + radius * math.cos(2 * math.pi * index / len(nodes)),
                                  center[1] + radius * math.sin(2 * math.pi * index / len(nodes))) for index, row in enumerate(nodes)}
        for edge in payload.get("edges", []):
            if edge["source"] in positions and edge["target"] in positions:
                x1, y1 = positions[edge["source"]]; x2, y2 = positions[edge["target"]]
                self.canvas.create_line(x1, y1, x2, y2, fill="#334155", width=1)
        for index, row in enumerate(nodes):
            x, y = positions[row["id"]]; color = self.COLORS.get(row["type"], "#CBD5E1"); tag = f"node-{index}"
            self.canvas.create_oval(x-8, y-8, x+8, y+8, fill=color, outline="#F8FAFC", tags=(tag,))
            self.canvas.create_text(x, y+18, text=row["label"][:24], fill="#E2E8F0", font=("Segoe UI", 8), tags=(tag,))
            self.canvas.tag_bind(tag, "<Button-1>", lambda _event, node_id=row["id"]: self.focus_node(node_id))

    def focus_node(self, node_id: str) -> None:
        result = self.service.neighbors(node_id, depth=1)
        if not result.get("ok"): return
        self.navigation.append(node_id)
        node = next(row for row in result["nodes"] if row["id"] == node_id)
        self.current = {**result, "available": self.service.snapshot()["available"]}
        self._render(self.current)
        self.details.configure(state="normal"); self.details.delete("1.0", "end")
        self.details.insert("1.0", json.dumps(node, indent=2, ensure_ascii=False)); self.details.configure(state="disabled")

    def back(self) -> None:
        if self.navigation: self.navigation.pop()
        if self.navigation: self.focus_node(self.navigation.pop())
        else: self.reload()

    def _tree_select(self, _event=None) -> None:
        selected = self.nodes.selection()
        if selected: self.focus_node(selected[0])
