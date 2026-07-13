"""Unified review and approval inbox for the existing native desktop shell."""

from __future__ import annotations

import json
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk
from typing import Any, Mapping

from secondbrain.agent.review_service import UnifiedReviewInbox


TAB_ALL = "Alle"
TAB_APPROVALS = "Freigaben"
TAB_REVIEWS = "Prüfungen"
TAB_DEFERRED = "Zurückgestellt"
TAB_COMPLETED = "Erledigt"
INBOX_TABS = (TAB_ALL, TAB_APPROVALS, TAB_REVIEWS, TAB_DEFERRED, TAB_COMPLETED)

_SENSITIVE_KEYS = ("password", "secret", "token", "api_key", "authorization", "cookie", "credential")


class ApprovalInboxViewModel:
    """Tk-free controller used by both the frame and headless tests."""

    def __init__(self, project_root: str | Path, *, inbox: UnifiedReviewInbox | None = None) -> None:
        self.project_root = Path(project_root).resolve()
        self.inbox = inbox or UnifiedReviewInbox(self.project_root)

    def load(self, tab: str = TAB_ALL) -> dict[str, Any]:
        if tab not in INBOX_TABS:
            raise ValueError(f"unknown_inbox_tab:{tab}")
        try:
            self._ensure_queue_health()
            all_items = self.inbox.list_all()
            items = self._filter_tab(all_items, tab)
            pending = [item for item in all_items if item["status"] == "pending"]
            critical = [item for item in pending if self.is_critical(item)]
            return {
                "ok": True,
                "status": "ready",
                "tab": tab,
                "items": [self._list_item(item) for item in items],
                "pending_count": len(pending),
                "critical_count": len(critical),
                "empty_message": self.empty_message(tab),
            }
        except Exception as exc:  # noqa: BLE001 - GUI boundary returns controlled state
            return {
                "ok": False,
                "status": "error",
                "tab": tab,
                "items": [],
                "pending_count": 0,
                "critical_count": 0,
                "empty_message": "Fehler beim Laden",
                "error": f"{type(exc).__name__}: {exc}",
            }

    def detail(self, item_id: str) -> dict[str, Any]:
        item = self.inbox.get(item_id)
        if item is None:
            raise KeyError(f"inbox_item_not_found:{item_id}")
        approval = self.inbox.approvals.get(item["item_id"]) if item["item_type"] == "approval" else None
        review = self._linked_review(approval, item_id)
        metadata = review.get("metadata") if isinstance((review or {}).get("metadata"), Mapping) else {}
        payload = approval.get("payload") if isinstance((approval or {}).get("payload"), Mapping) else {}
        secrets = self._sensitive_values(payload)
        safe_item = self.redact(item, secrets=secrets)
        audit = []
        if approval is not None:
            audit.extend(approval.get("decision_audit") or [])
        if review is not None:
            audit.extend(review.get("decision_audit") or [])
        audit.sort(key=lambda row: str(row.get("timestamp") or ""))
        tool = str((approval or {}).get("tool_name") or (approval or {}).get("command") or metadata.get("tool_name") or "")
        plan_id = str(item.get("plan_id") or metadata.get("plan_id") or "")
        step_id = str(item.get("step_id") or metadata.get("step_id") or "")
        return {
            **safe_item,
            "description": safe_item["description"],
            "payload": self.redact(payload, secrets=secrets),
            "tool": tool,
            "risk": item["risk_level"],
            "reason": self.redact(str((approval or {}).get("reason") or item["description"]), secrets=secrets),
            "plan_step": f"{plan_id}:{step_id}" if plan_id or step_id else "",
            "plan_id": plan_id,
            "step_id": step_id,
            "audit_history": self.redact(audit, secrets=secrets),
            "source_target": self._source_target(item, review),
            "source_openable": bool(self._source_target(item, review)),
            "plan_openable": bool(plan_id),
            "warning": self.approval_warning(item, tool),
        }

    def approve(self, item_id: str, actor: str = "desktop_user", note: str = "") -> dict[str, Any]:
        return self.inbox.approve(item_id, actor, note)

    def reject(self, item_id: str, actor: str = "desktop_user", note: str = "") -> dict[str, Any]:
        return self.inbox.reject(item_id, actor, note)

    def defer(
        self,
        item_id: str,
        actor: str = "desktop_user",
        until: str = "",
        note: str = "",
    ) -> dict[str, Any]:
        return self.inbox.defer(item_id, actor, until=until, note=note)

    def snapshot(self) -> dict[str, Any]:
        state = self.load()
        return {
            "ok": state["ok"],
            "status": state["status"],
            "pending_count": state["pending_count"],
            "critical_count": state["critical_count"],
            "items": state["items"],
            "error": state.get("error", ""),
        }

    def _ensure_queue_health(self) -> None:
        rows = [*self.inbox.approvals.list(), *self.inbox.reviews.list()]
        if any(row.get("status") == "invalid_json" for row in rows):
            raise RuntimeError("review_approval_queue_corrupt")

    @staticmethod
    def _filter_tab(items: list[dict[str, Any]], tab: str) -> list[dict[str, Any]]:
        if tab == TAB_APPROVALS:
            return [item for item in items if item["item_type"] == "approval" and item["status"] == "pending"]
        if tab == TAB_REVIEWS:
            return [item for item in items if item["item_type"] == "review" and item["status"] == "pending"]
        if tab == TAB_DEFERRED:
            return [item for item in items if item["status"] == "deferred"]
        if tab == TAB_COMPLETED:
            return [item for item in items if item["status"] not in {"pending", "deferred"}]
        return items

    def _list_item(self, item: dict[str, Any]) -> dict[str, Any]:
        approval = self.inbox.approvals.get(str(item.get("item_id") or "")) if item.get("item_type") == "approval" else None
        payload = approval.get("payload") if isinstance((approval or {}).get("payload"), Mapping) else {}
        safe_item = self.redact(item, secrets=self._sensitive_values(payload))
        return {
            key: safe_item[key]
            for key in (
                "item_id",
                "item_type",
                "category",
                "status",
                "title",
                "source",
                "risk_level",
                "created_at",
                "target",
                "actions_allowed",
            )
        } | {"critical": self.is_critical(item)}

    def _linked_review(self, approval: dict[str, Any] | None, requested_id: str) -> dict[str, Any] | None:
        if approval is not None:
            review_id = str(approval.get("review_id") or "")
            if review_id:
                return self.inbox.reviews.get(review_id)
            approval_id = str(approval.get("approval_id") or "")
            return next((row for row in self.inbox.reviews.list() if row.get("approval_id") == approval_id), None)
        return self.inbox.reviews.get(requested_id)

    @staticmethod
    def _source_target(item: dict[str, Any], review: dict[str, Any] | None) -> str:
        metadata = review.get("metadata") if isinstance((review or {}).get("metadata"), Mapping) else {}
        candidate = str(metadata.get("source_path") or item.get("target") or "")
        path = Path(candidate).expanduser() if candidate else None
        return str(path.resolve()) if path is not None and path.exists() else ""

    @staticmethod
    def empty_message(tab: str) -> str:
        if tab == TAB_DEFERRED:
            return "Keine zurückgestellten Einträge"
        if tab == TAB_COMPLETED:
            return "Keine erledigten Einträge"
        return "Keine offenen Freigaben"

    @staticmethod
    def is_critical(item: Mapping[str, Any]) -> bool:
        return item.get("category") in {"delete_request", "connector_permission_change", "sensitive_document"} or item.get(
            "risk_level"
        ) in {"high", "critical", "destructive"}

    @staticmethod
    def approval_warning(item: Mapping[str, Any], tool: str = "") -> str:
        warning = "Diese Aktion wird nach der Genehmigung ausgeführt."
        action = f"{item.get('category', '')} {tool}".lower()
        if "delete" in action:
            return f"WARNUNG: Löschaktion. {warning} Gelöschte Daten sind möglicherweise nicht wiederherstellbar."
        if "send" in action or "forward" in action:
            return f"WARNUNG: Sendeaktion. {warning} Externe Empfänger können die Daten erhalten."
        return warning

    @classmethod
    def redact(cls, value: Any, *, key: str = "", secrets: set[str] | None = None) -> Any:
        secrets = secrets or set()
        if key and any(token in key.lower() for token in _SENSITIVE_KEYS):
            return "***"
        if isinstance(value, Mapping):
            return {
                str(item_key): cls.redact(item, key=str(item_key), secrets=secrets)
                for item_key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [cls.redact(item, secrets=secrets) for item in value]
        if isinstance(value, str):
            redacted = value
            for secret in secrets:
                redacted = redacted.replace(secret, "***")
            return redacted
        return value

    @classmethod
    def _sensitive_values(cls, value: Any, *, key: str = "") -> set[str]:
        if key and any(token in key.lower() for token in _SENSITIVE_KEYS):
            rendered = "" if value is None else str(value)
            return {rendered} if rendered not in {"", "***"} else set()
        if isinstance(value, Mapping):
            secrets = set()
            for item_key, item in value.items():
                secrets.update(cls._sensitive_values(item, key=str(item_key)))
            return secrets
        if isinstance(value, (list, tuple)):
            secrets = set()
            for item in value:
                secrets.update(cls._sensitive_values(item))
            return secrets
        return set()


class ApprovalInboxFrame(ttk.Frame):
    """Embedded inbox panel for AIWorkspaceApp; never creates another root window."""

    COLUMNS = ("category", "title", "source", "risk", "status", "created", "target")

    def __init__(
        self,
        master: tk.Misc,
        project_root: str | Path,
        *,
        navigate_callback: Any = None,
        changed_callback: Any = None,
        view_model: ApprovalInboxViewModel | None = None,
    ) -> None:
        super().__init__(master, padding=8)
        self.view_model = view_model or ApprovalInboxViewModel(project_root)
        self.navigate_callback = navigate_callback
        self.changed_callback = changed_callback
        self.current_item_id = ""
        self.processing = False
        self.badge_var = tk.StringVar(value="0 offen")
        self.message_var = tk.StringVar(value="")
        self.trees: dict[str, ttk.Treeview] = {}
        self.action_buttons: list[ttk.Button] = []
        self._build()
        self.reload()

    def _build(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 6))
        ttk.Label(header, text="Prüfungen & Freigaben", font=("Segoe UI", 13, "bold")).pack(side="left")
        ttk.Label(header, textvariable=self.badge_var).pack(side="left", padx=10)
        ttk.Button(header, text="Aktualisieren", command=self.reload).pack(side="right")

        body = ttk.PanedWindow(self, orient="horizontal")
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body)
        right = ttk.Frame(body, padding=(8, 0, 0, 0))
        body.add(left, weight=3)
        body.add(right, weight=2)

        self.tabs = ttk.Notebook(left)
        self.tabs.pack(fill="both", expand=True)
        self.tabs.bind("<<NotebookTabChanged>>", lambda _event: self._tab_changed())
        for tab in INBOX_TABS:
            frame = ttk.Frame(self.tabs)
            tree = ttk.Treeview(frame, columns=self.COLUMNS, show="headings", selectmode="browse")
            headings = {
                "category": "Kategorie",
                "title": "Titel",
                "source": "Quelle",
                "risk": "Risiko",
                "status": "Status",
                "created": "Erstellt",
                "target": "Ziel",
            }
            widths = {"category": 145, "title": 220, "source": 100, "risk": 70, "status": 90, "created": 145, "target": 150}
            for column in self.COLUMNS:
                tree.heading(column, text=headings[column])
                tree.column(column, width=widths[column], stretch=column in {"title", "target"})
            tree.tag_configure("critical", background="#5A1A1A", foreground="#FFFFFF")
            tree.bind("<<TreeviewSelect>>", self._select_item)
            scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scroll.set)
            scroll.pack(side="right", fill="y")
            tree.pack(side="left", fill="both", expand=True)
            self.tabs.add(frame, text=tab)
            self.trees[tab] = tree

        self.detail = tk.Text(right, wrap="word", state="disabled", width=48)
        self.detail.pack(fill="both", expand=True)
        actions = ttk.Frame(right)
        actions.pack(fill="x", pady=6)
        for label, command in (
            ("Genehmigen", self._approve),
            ("Ablehnen", self._reject),
            ("Zurückstellen", self._defer),
        ):
            button = ttk.Button(actions, text=label, command=command)
            button.pack(side="left", padx=2)
            self.action_buttons.append(button)
        self.source_button = ttk.Button(actions, text="Quelle öffnen", command=self._open_source)
        self.source_button.pack(side="left", padx=(12, 2))
        self.plan_button = ttk.Button(actions, text="Plan anzeigen", command=self._show_plan)
        self.plan_button.pack(side="left", padx=2)
        self.action_buttons.extend([self.source_button, self.plan_button])
        ttk.Label(right, textvariable=self.message_var).pack(fill="x")

    def reload(self) -> None:
        selected = self.current_item_id
        error = ""
        pending_count = 0
        critical_count = 0
        for tab, tree in self.trees.items():
            state = self.view_model.load(tab)
            pending_count = max(pending_count, int(state["pending_count"]))
            critical_count = max(critical_count, int(state["critical_count"]))
            tree.delete(*tree.get_children())
            if not state["ok"]:
                error = state.get("error") or "Fehler beim Laden"
                continue
            for item in state["items"]:
                tree.insert(
                    "",
                    "end",
                    iid=f"{tab}:{item['item_id']}",
                    values=(
                        item["category"],
                        item["title"],
                        item["source"],
                        item["risk_level"],
                        item["status"],
                        item["created_at"],
                        item["target"],
                    ),
                    tags=("critical",) if item["critical"] else (),
                )
            if not state["items"]:
                tree.insert("", "end", iid=f"{tab}:__empty__", values=("", state["empty_message"], "", "", "", "", ""))
        critical_suffix = f" · {critical_count} kritisch" if critical_count else ""
        self.badge_var.set(f"{pending_count} offen{critical_suffix}")
        self.message_var.set(f"Fehler beim Laden: {error}" if error else "")
        if selected:
            self._render_detail(selected)

    def _tab_changed(self) -> None:
        self.current_item_id = ""
        self._write_detail({"Hinweis": self.view_model.empty_message(self.tabs.tab(self.tabs.select(), "text"))})

    def _select_item(self, _event: object | None = None) -> None:
        tab = self.tabs.tab(self.tabs.select(), "text")
        selected = self.trees[tab].selection()
        if not selected or selected[0].endswith(":__empty__"):
            return
        self.current_item_id = selected[0].split(":", 1)[1]
        self._render_detail(self.current_item_id)

    def _render_detail(self, item_id: str) -> None:
        try:
            detail = self.view_model.detail(item_id)
        except Exception as exc:  # noqa: BLE001 - controlled GUI error state
            self.message_var.set(f"Fehler beim Laden: {type(exc).__name__}: {exc}")
            return
        self._write_detail(
            {
                "Beschreibung": detail["description"],
                "Sanitierte Payload": detail["payload"],
                "Tool": detail["tool"],
                "Risiko": detail["risk"],
                "Begründung": detail["reason"],
                "Plan-Schritt": detail["plan_step"],
                "Plan-ID": detail["plan_id"],
                "Audit-Verlauf": detail["audit_history"],
            }
        )
        self.source_button.configure(state="normal" if detail["source_openable"] else "disabled")
        self.plan_button.configure(state="normal" if detail["plan_openable"] else "disabled")

    def _write_detail(self, payload: Mapping[str, Any]) -> None:
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("1.0", json.dumps(payload, indent=2, ensure_ascii=False, default=str))
        self.detail.configure(state="disabled")

    def _approve(self) -> None:
        if not self.current_item_id:
            return
        detail = self.view_model.detail(self.current_item_id)
        if not messagebox.askyesno("Freigabe bestätigen", detail["warning"], parent=self):
            return
        self._process(lambda: self.view_model.approve(self.current_item_id, note="Desktop confirmation"))

    def _reject(self) -> None:
        if self.current_item_id:
            self._process(lambda: self.view_model.reject(self.current_item_id, note="Desktop rejection"))

    def _defer(self) -> None:
        if not self.current_item_id:
            return
        until = simpledialog.askstring("Zurückstellen", "Bis wann? (ISO-Zeit, optional)", parent=self) or ""
        self._process(lambda: self.view_model.defer(self.current_item_id, until=until, note="Desktop defer"))

    def _process(self, operation: Any) -> None:
        if self.processing:
            return
        self.processing = True
        self._set_buttons("disabled")
        self.update_idletasks()
        try:
            operation()
            self.current_item_id = ""
            self.message_var.set("Entscheidung gespeichert")
            self.reload()
            if self.changed_callback is not None:
                self.changed_callback()
        except Exception as exc:  # noqa: BLE001 - controlled GUI error state
            self.message_var.set(f"Aktion fehlgeschlagen: {type(exc).__name__}: {exc}")
            messagebox.showerror("Aktion fehlgeschlagen", str(exc), parent=self)
        finally:
            self.processing = False
            self._set_buttons("normal")

    def _set_buttons(self, state: str) -> None:
        for button in self.action_buttons:
            button.configure(state=state)

    def _open_source(self) -> None:
        if not self.current_item_id:
            return
        target = self.view_model.detail(self.current_item_id)["source_target"]
        if target:
            webbrowser.open(Path(target).as_uri())

    def _show_plan(self) -> None:
        if not self.current_item_id:
            return
        detail = self.view_model.detail(self.current_item_id)
        if detail["plan_id"] and self.navigate_callback is not None:
            self.navigate_callback("tasks")


class ApprovalInbox:
    """Compatibility adapter for the former minimal render API."""

    def render(self, approvals: list[dict[str, Any]]) -> dict[str, Any]:
        return {"pending": len(approvals), "items": approvals}
