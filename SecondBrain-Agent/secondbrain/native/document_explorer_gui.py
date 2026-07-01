from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, simpledialog

from .document_explorer import DocumentExplorer


def run_document_explorer_gui(project_root: str | Path = '.') -> int:
    explorer = DocumentExplorer(project_root)
    root = tk.Tk()
    root.title('Jarvis Dokumente')
    root.geometry('1100x720')

    query_var = tk.StringVar()
    status_var = tk.StringVar(value='Bereit')

    top = ttk.Frame(root, padding=8)
    top.pack(fill=tk.X)
    ttk.Label(top, text='Suche').pack(side=tk.LEFT)
    entry = ttk.Entry(top, textvariable=query_var, width=45)
    entry.pack(side=tk.LEFT, padx=8)

    columns = ('name', 'extension', 'size', 'parser', 'ocr', 'index', 'tags')
    tree = ttk.Treeview(root, columns=columns, show='headings')
    for col, text, width in [
        ('name', 'Name', 260), ('extension', 'Typ', 70), ('size', 'Größe', 90),
        ('parser', 'Parser', 120), ('ocr', 'OCR', 100), ('index', 'Index', 100), ('tags', 'Tags', 220),
    ]:
        tree.heading(col, text=text)
        tree.column(col, width=width, anchor=tk.W)
    tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

    bottom = ttk.Frame(root, padding=8)
    bottom.pack(fill=tk.BOTH)
    preview = tk.Text(bottom, height=10, wrap=tk.WORD)
    preview.pack(fill=tk.BOTH, expand=True)

    rows: list[dict] = []

    def refresh() -> None:
        nonlocal rows
        for child in tree.get_children():
            tree.delete(child)
        payload = explorer.list_documents(query=query_var.get(), limit=500)
        rows = payload.get('documents', [])
        for idx, row in enumerate(rows):
            tree.insert('', tk.END, iid=str(idx), values=(
                row.get('name'), row.get('extension'), row.get('size_bytes'), row.get('parser_hint'),
                row.get('ocr_status'), row.get('index_status'), ', '.join(row.get('tags') or []),
            ))
        status_var.set(f"{payload.get('count', 0)} Dokumente")

    def show_preview(_event=None) -> None:
        selected = tree.selection()
        preview.delete('1.0', tk.END)
        if not selected:
            return
        row = rows[int(selected[0])]
        payload = explorer.preview(row['document_id'])
        if payload.get('preview'):
            preview.insert(tk.END, payload['preview'])
        else:
            preview.insert(tk.END, json.dumps(payload, ensure_ascii=False, indent=2))

    def tag_selected() -> None:
        selected = tree.selection()
        if not selected:
            messagebox.showinfo('Jarvis Dokumente', 'Kein Dokument ausgewählt.')
            return
        row = rows[int(selected[0])]
        tags = simpledialog.askstring('Tags', 'Tags kommagetrennt eingeben:')
        if tags is None:
            return
        explorer.tag(row['document_id'], [part.strip() for part in tags.split(',')])
        refresh()

    ttk.Button(top, text='Aktualisieren', command=refresh).pack(side=tk.LEFT, padx=4)
    ttk.Button(top, text='Suchen', command=refresh).pack(side=tk.LEFT, padx=4)
    ttk.Button(top, text='Tag setzen', command=tag_selected).pack(side=tk.LEFT, padx=4)
    ttk.Label(root, textvariable=status_var, padding=6).pack(fill=tk.X)

    entry.bind('<Return>', lambda _event: refresh())
    tree.bind('<<TreeviewSelect>>', show_preview)
    refresh()
    root.mainloop()
    return 0
