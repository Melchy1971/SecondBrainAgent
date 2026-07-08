"""v30.47 - Document Preview Center GUI.

Ein einbettbares Tk-Frame fuer den AI Workspace (MITTE-Zone) plus ein
Standalone-Start. Kein zweiter Dokumentkatalog: die Liste kommt aus dem
DocumentExplorer, das Parsing aus document_understanding.

Rendering-Strategie:
- PDF:    PyMuPDF-Pixmap -> PNG -> tk.PhotoImage (Zoom = Neu-Rendern), sonst Text
- Bilder: Pillow-Resize -> PNG -> tk.PhotoImage, sonst Statushinweis
- Text/Markdown/JSON/CSV/DOCX/XLSX: Parser-Text im Text-Widget (Zoom = Fontgroesse)

OS-Drag&Drop laeuft optional ueber tkinterdnd2; ohne Paket bleiben Import-Button
und Kontextmenue der Weg in den Bestand.
"""
from __future__ import annotations

import base64
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, simpledialog, ttk
from typing import Any

from .models import IMAGE_EXTENSIONS, PreviewState, ZoomModel
from .service import DocumentPreviewService

BASE_FONT_SIZE = 10


class DocumentPreviewFrame(ttk.Frame):
    """Vorschau-Oberflaeche: Liste links, Vorschau rechts, eine Toolbar oben."""

    def __init__(self, master: tk.Misc, project_root: str | Path = ".",
                 state_sink: Any = None) -> None:
        super().__init__(master, padding=4)
        self.service = DocumentPreviewService(project_root)
        self.state = PreviewState()
        self.state_sink = state_sink  # ApplicationState des AI Workspace (optional)
        self._photo: tk.PhotoImage | None = None
        self._current_preview: dict[str, Any] = {}
        self._drag_document: str | None = None
        self._build()
        self.reload_documents()

    # --- Aufbau -----------------------------------------------------------------

    def _build(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x")
        self.search_var = tk.StringVar()
        ttk.Label(toolbar, text="Suche").pack(side="left")
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=24)
        search_entry.pack(side="left", padx=4)
        search_entry.bind("<Return>", lambda _e: self.run_search())
        ttk.Button(toolbar, text="Suchen", command=self.run_search).pack(side="left")
        ttk.Button(toolbar, text="-", width=3, command=self.zoom_out).pack(side="left", padx=(12, 0))
        self.zoom_label = ttk.Label(toolbar, text="100%", width=6, anchor="center")
        self.zoom_label.pack(side="left")
        ttk.Button(toolbar, text="+", width=3, command=self.zoom_in).pack(side="left")
        ttk.Button(toolbar, text="<", width=3, command=lambda: self.goto_page(self.state.page - 1)).pack(side="left", padx=(12, 0))
        self.page_label = ttk.Label(toolbar, text="1/1", width=8, anchor="center")
        self.page_label.pack(side="left")
        ttk.Button(toolbar, text=">", width=3, command=lambda: self.goto_page(self.state.page + 1)).pack(side="left")
        self.overlay_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(toolbar, text="OCR Overlay", variable=self.overlay_var,
                        command=self.toggle_overlay).pack(side="left", padx=(12, 0))
        ttk.Button(toolbar, text="Metadaten", command=self.show_metadata).pack(side="left", padx=(12, 0))
        ttk.Button(toolbar, text="Versionen", command=self.show_versions).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Import", command=self.import_file).pack(side="right")

        body = tk.PanedWindow(self, orient="horizontal", sashwidth=4)
        body.pack(fill="both", expand=True, pady=(6, 0))

        list_frame = ttk.Frame(body)
        self.doc_filter_var = tk.StringVar()
        filter_entry = ttk.Entry(list_frame, textvariable=self.doc_filter_var)
        filter_entry.pack(fill="x")
        filter_entry.bind("<KeyRelease>", lambda _e: self.reload_documents())
        self.doc_list = tk.Listbox(list_frame, exportselection=False)
        self.doc_list.pack(fill="both", expand=True)
        self.doc_list.bind("<<ListboxSelect>>", lambda _e: self.open_selected())
        self.doc_list.bind("<Button-3>", self._show_list_menu)
        self.doc_list.bind("<ButtonPress-1>", self._drag_start)
        self.doc_list.bind("<ButtonRelease-1>", self._drag_release)
        body.add(list_frame, width=260)

        preview_frame = ttk.Frame(body)
        self.canvas = tk.Canvas(preview_frame, background="#1E293B", highlightthickness=0)
        self.text = tk.Text(preview_frame, wrap="word", state="disabled",
                            font=("Consolas", BASE_FONT_SIZE))
        self.text.tag_configure("hit", background="#FDE047", foreground="#111827")
        self.canvas.bind("<Button-3>", self._show_preview_menu)
        self.text.bind("<Button-3>", self._show_preview_menu)
        self.canvas.bind("<Control-MouseWheel>", self._wheel_zoom)
        self.text.bind("<Control-MouseWheel>", self._wheel_zoom)
        body.add(preview_frame, stretch="always")
        self.preview_frame = preview_frame

        self.info_var = tk.StringVar(value="Kein Dokument geoeffnet")
        ttk.Label(self, textvariable=self.info_var, anchor="w").pack(fill="x", pady=(4, 0))

        self._list_menu = tk.Menu(self, tearoff=0)
        self._list_menu.add_command(label="Oeffnen", command=self.open_selected)
        self._list_menu.add_command(label="Metadaten", command=self.show_metadata)
        self._list_menu.add_command(label="Version sichern", command=self.snapshot_version)
        self._list_menu.add_command(label="Annotieren", command=self.add_annotation)
        self._list_menu.add_command(label="In Chat-Auswahl", command=self.send_to_chat_selection)
        self._preview_menu = tk.Menu(self, tearoff=0)
        self._preview_menu.add_command(label="Zoom zuruecksetzen", command=self.zoom_reset)
        self._preview_menu.add_command(label="OCR Overlay umschalten", command=self._toggle_overlay_from_menu)
        self._preview_menu.add_command(label="Annotieren", command=self.add_annotation)
        self._preview_menu.add_command(label="Version sichern", command=self.snapshot_version)

        self._register_os_drop_target()

    def _register_os_drop_target(self) -> None:
        """OS-Drag&Drop nur, wenn tkinterdnd2 vorhanden UND die Root-Instanz es traegt."""
        try:
            from tkinterdnd2 import DND_FILES  # type: ignore[import-not-found]

            root = self.winfo_toplevel()
            if not hasattr(root, "drop_target_register"):
                return
            for widget in (self.doc_list, self.canvas, self.text):
                widget.drop_target_register(DND_FILES)  # type: ignore[attr-defined]
                widget.dnd_bind("<<Drop>>", self._on_os_drop)  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001 - DnD bleibt optional
            return

    # --- Dokumentliste -------------------------------------------------------------

    def reload_documents(self) -> None:
        query = self.doc_filter_var.get() if hasattr(self, "doc_filter_var") else ""
        listing = self.service.explorer.list_documents(query=query, limit=500)
        self.doc_list.delete(0, "end")
        self._documents = listing.get("documents", [])
        for row in self._documents:
            self.doc_list.insert("end", f"{row['name']}  [{row['extension']}]")

    def _selected_document(self) -> dict[str, Any] | None:
        selection = self.doc_list.curselection()
        if not selection:
            return None
        index = selection[0]
        if index >= len(self._documents):
            return None
        return self._documents[index]

    # --- Vorschau -------------------------------------------------------------------

    def open_selected(self) -> None:
        row = self._selected_document()
        if row is not None:
            self.open_document(row["path"])

    def open_document(self, document_ref: str) -> None:
        preview = self.service.preview(document_ref)
        self._current_preview = preview
        if not preview.get("ok"):
            self.info_var.set(f"Vorschau fehlgeschlagen: {preview.get('status')}")
            return
        self.state.document_id = preview.get("document_ref")
        self.state.path = preview.get("path")
        self.state.extension = preview.get("extension")
        self.state.page_count = int(preview.get("page_count", 1))
        self.state.set_page(1)
        self.render()

    def render(self) -> None:
        preview = self._current_preview
        if not preview:
            return
        renderer = preview.get("renderer", "text")
        if renderer == "canvas_pdf":
            self._render_pdf()
        elif renderer == "canvas_image":
            self._render_image()
        else:
            self._render_text()
        self.zoom_label.configure(text=f"{int(self.state.zoom * 100)}%")
        self.page_label.configure(text=f"{self.state.page}/{self.state.page_count}")
        status = preview.get("status", "")
        self.info_var.set(f"{preview.get('path', '')} | {status} | {preview.get('mime_type', '')}")

    def _show_canvas(self) -> None:
        self.text.pack_forget()
        self.canvas.pack(fill="both", expand=True)

    def _show_text(self) -> None:
        self.canvas.pack_forget()
        self.text.pack(fill="both", expand=True)

    def _render_pdf(self) -> None:
        try:
            import fitz  # type: ignore[import-not-found]

            with fitz.open(self.state.path) as doc:
                index = max(0, min(self.state.page - 1, doc.page_count - 1))
                pixmap = doc[index].get_pixmap(dpi=int(96 * self.state.zoom))
                png_bytes = pixmap.tobytes("png")
        except Exception as exc:  # noqa: BLE001 - Renderer degradiert zu Text
            self._render_text(prefix=f"[PDF-Rendering nicht verfuegbar: {type(exc).__name__}]\n\n")
            return
        self._show_canvas()
        self._photo = tk.PhotoImage(data=base64.b64encode(png_bytes).decode("ascii"))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self._photo, anchor="nw")
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        if self.state.overlay_enabled:
            self._draw_overlay()

    def _render_image(self) -> None:
        try:
            import io

            from PIL import Image  # type: ignore[import-not-found]

            with Image.open(self.state.path) as image:
                width = max(1, int(image.width * self.state.zoom))
                height = max(1, int(image.height * self.state.zoom))
                resized = image.convert("RGB").resize((width, height))
                buffer = io.BytesIO()
                resized.save(buffer, format="PNG")
        except Exception as exc:  # noqa: BLE001 - Renderer degradiert zu Text
            self._render_text(prefix=f"[Bild-Rendering nicht verfuegbar: {type(exc).__name__}]\n\n")
            return
        self._show_canvas()
        self._photo = tk.PhotoImage(data=base64.b64encode(buffer.getvalue()).decode("ascii"))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self._photo, anchor="nw")
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        if self.state.overlay_enabled:
            self._draw_overlay()

    def _render_text(self, prefix: str = "") -> None:
        preview = self._current_preview
        pages = preview.get("pages") or []
        if pages and 0 < self.state.page <= len(pages):
            content = pages[self.state.page - 1].get("text", "")
        else:
            content = preview.get("text", "")
        if preview.get("status") == "ocr_required" and not content:
            content = "[Kein extrahierbarer Text - OCR erforderlich. OCR Overlay aktivieren oder OCR-Engine installieren.]"
        self._show_text()
        font_size = max(6, int(BASE_FONT_SIZE * self.state.zoom))
        self.text.configure(state="normal", font=("Consolas", font_size))
        self.text.delete("1.0", "end")
        self.text.insert("1.0", prefix + content)
        self._highlight_hits()
        self.text.configure(state="disabled")

    def _highlight_hits(self) -> None:
        query = (self.state.search_query or "").strip()
        if not query:
            return
        start = "1.0"
        while True:
            found = self.text.search(query, start, stopindex="end", nocase=True)
            if not found:
                break
            end = f"{found}+{len(query)}c"
            self.text.tag_add("hit", found, end)
            start = end

    def _draw_overlay(self) -> None:
        payload = self.service.ocr_overlay(self.state.path or "", page=self.state.page)
        status = payload.get("status")
        if status != "overlay":
            self.info_var.set(f"OCR Overlay: {status}")
            return
        scale = self.state.zoom if (self.state.extension in IMAGE_EXTENSIONS) else (96.0 / 150.0) * self.state.zoom
        for item in payload.get("items", []):
            x0, y0, x1, y1 = (value * scale for value in item["bbox"])
            self.canvas.create_rectangle(x0, y0, x1, y1, outline="#22D3EE")
            self.canvas.create_text(x0, max(0, y0 - 7), text=item["text"], anchor="sw",
                                    fill="#22D3EE", font=("Segoe UI", 7))

    # --- Interaktion ------------------------------------------------------------------

    def zoom_in(self) -> None:
        self.state.set_zoom(ZoomModel.zoom_in(self.state.zoom))
        self.render()

    def zoom_out(self) -> None:
        self.state.set_zoom(ZoomModel.zoom_out(self.state.zoom))
        self.render()

    def zoom_reset(self) -> None:
        self.state.set_zoom(ZoomModel.DEFAULT)
        self.render()

    def _wheel_zoom(self, event: Any) -> None:
        if getattr(event, "delta", 0) > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def goto_page(self, page: int) -> None:
        self.state.set_page(page)
        self.render()

    def run_search(self) -> None:
        self.state.search_query = self.search_var.get()
        if not self.state.path:
            return
        payload = self.service.search(self.state.path, self.state.search_query)
        self.state.search_hits = payload.get("hits", [])
        if self.state.search_hits:
            first = self.state.search_hits[0]
            self.state.set_page(int(first.get("page", 1)))
            self.info_var.set(f"Suche '{self.state.search_query}': {payload.get('count', 0)} Treffer")
        else:
            self.info_var.set(f"Suche '{self.state.search_query}': keine Treffer")
        self.render()

    def toggle_overlay(self) -> None:
        self.state.overlay_enabled = bool(self.overlay_var.get())
        self.render()

    def _toggle_overlay_from_menu(self) -> None:
        self.overlay_var.set(not self.overlay_var.get())
        self.toggle_overlay()

    def show_metadata(self) -> None:
        ref = self._context_ref()
        if ref is None:
            return
        payload = self.service.metadata(ref)
        self._show_payload_window("Metadaten", payload)

    def show_versions(self) -> None:
        ref = self._context_ref()
        if ref is None:
            return
        payload = self.service.versions(ref)
        self._show_payload_window("Versionen", payload)

    def snapshot_version(self) -> None:
        ref = self._context_ref()
        if ref is None:
            return
        payload = self.service.snapshot_version(ref)
        self.info_var.set(f"Version: {payload.get('status')}")

    def add_annotation(self) -> None:
        ref = self._context_ref()
        if ref is None:
            return
        text = simpledialog.askstring("Annotation", "Text der Annotation:", parent=self)
        if not text:
            return
        payload = self.service.annotate(ref, text, page=self.state.page)
        self.info_var.set(f"Annotation: {payload.get('status')}")

    def send_to_chat_selection(self) -> None:
        """Uebergibt das Dokument an die bestehende Chat-Auswahl des AI Workspace."""
        row = self._selected_document()
        if row is None or self.state_sink is None:
            return
        self.state_sink.selected_documents = [str(row["path"])]
        self.state_sink.message = f"Dokument fuer Chat ausgewaehlt: {row['name']}"

    def import_file(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Unterstuetzt", "*.pdf *.docx *.xlsx *.csv *.txt *.png *.jpg *.jpeg *.md *.json")]
        )
        if not path:
            return
        payload = self.service.import_dropped_file(path)
        self.info_var.set(f"Import: {payload.get('status')}")
        self.reload_documents()

    def _on_os_drop(self, event: Any) -> None:
        raw = str(getattr(event, "data", "")).strip()
        if not raw:
            return
        for candidate in self.tk.splitlist(raw):
            payload = self.service.import_dropped_file(candidate)
            self.info_var.set(f"Drop-Import: {payload.get('status')}")
        self.reload_documents()

    # interner Drag&Drop: Listeneintrag auf die Vorschau ziehen -> oeffnen
    def _drag_start(self, event: Any) -> None:
        index = self.doc_list.nearest(event.y)
        if 0 <= index < len(getattr(self, "_documents", [])):
            self._drag_document = self._documents[index]["path"]

    def _drag_release(self, event: Any) -> None:
        if self._drag_document is None:
            return
        target = self.winfo_containing(event.x_root, event.y_root)
        if target in {self.canvas, self.text}:
            self.open_document(self._drag_document)
        self._drag_document = None

    def _context_ref(self) -> str | None:
        if self.state.path:
            return self.state.path
        row = self._selected_document()
        return row["path"] if row else None

    def _show_list_menu(self, event: Any) -> None:
        index = self.doc_list.nearest(event.y)
        if 0 <= index < self.doc_list.size():
            self.doc_list.selection_clear(0, "end")
            self.doc_list.selection_set(index)
        self._post_menu(self._list_menu, event)

    def _show_preview_menu(self, event: Any) -> None:
        self._post_menu(self._preview_menu, event)

    @staticmethod
    def _post_menu(menu: tk.Menu, event: Any) -> None:
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _show_payload_window(self, title: str, payload: dict[str, Any]) -> None:
        import json

        window = tk.Toplevel(self)
        window.title(title)
        window.geometry("560x420")
        text = tk.Text(window, wrap="word")
        text.pack(fill="both", expand=True)
        text.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        text.configure(state="disabled")


def run_gui(project_root: str | Path = ".") -> int:
    """Standalone-Start; nutzt tkinterdnd2-Root wenn vorhanden (OS-Drag&Drop)."""
    root: tk.Tk
    try:
        from tkinterdnd2 import TkinterDnD  # type: ignore[import-not-found]

        root = TkinterDnD.Tk()
    except Exception:  # noqa: BLE001 - DnD bleibt optional
        root = tk.Tk()
    root.title("Document Preview Center")
    root.geometry("1200x760")
    frame = DocumentPreviewFrame(root, project_root)
    frame.pack(fill="both", expand=True)
    root.mainloop()
    return 0
