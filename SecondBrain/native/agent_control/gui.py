"""v30.66 Native Agent Control - GUI panel.

Renders the eight agent areas as tabs inside the native AI Workspace shell. This
is NOT a second application: ``AgentControlPanel`` is a ``ttk.Frame`` meant to be
embedded, and ``run_gui`` is only a standalone dev/preview entry point. All data
comes from :class:`AgentControlService` (UI-free ``view_model``), so the panel
holds no logic of its own. Tkinter is imported lazily so the module imports in
headless/test environments.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .service import AREAS, AgentControlService


def build_tabs(service: AgentControlService) -> list[dict[str, Any]]:
    """UI-free description of the tabs the GUI renders (testable)."""
    vm = service.view_model()
    return [{"id": area["id"], "title": area["title"], "ok": area["ok"],
             "lines": _area_lines(area["id"], area["data"])}
            for area in vm["areas"]]


def _area_lines(area_id: str, data: dict[str, Any]) -> list[str]:
    if not data.get("ok"):
        return [f"nicht verfügbar: {data.get('error') or data.get('status')}"]
    if area_id == "plans":
        return [
            f"{p['id']}  [{p['status']}]  {p['steps_completed']}/{p['steps']}  risk:{p.get('maximum_risk','low')}  gates:{p.get('approval_gates',0)}  wait:{p.get('waiting_approval',0)}  fail:{p.get('failed_steps',0)}  deps:{p.get('dependencies',0)}  {p['goal'][:40]}"
                for p in data.get("plans", [])] or ["keine Pläne"]
    if area_id == "workflows":
        return [f"{w['workflow_id']}  [{w['state']}]  {w['steps_completed']}/{w['steps']}"
                for w in data.get("workflows", [])] or ["keine Workflows"]
    if area_id == "background_agents":
        return [f"{a['id']}  [{a['state']}]  {a['agent_type']}"
                for a in data.get("agents", [])] or ["keine Background Agents"]
    if area_id == "approvals":
        return [f"{a['approval_id']}  {a.get('command','')}  [{a.get('risk_level','')}]  {a.get('status','pending')}  {a.get('category','risky_agent_action')}"
                for a in data.get("approvals", [])] or ["keine offenen Approvals"]
    if area_id == "goals":
        return [f"{g['id']}  [{g['status']}]  {round(g['progress']*100)}%  {g['title'][:40]}"
                for g in data.get("goals", [])] or ["keine Goals"]
    if area_id == "audit":
        return [f"{name}: {info['count']} Einträge" for name, info in data.get("trails", {}).items()]
    if area_id == "logs":
        return [f"{r.get('ts','')}  {r.get('event','')}" for r in data.get("logs", [])] or ["keine Logs"]
    if area_id == "agents":
        return [f"Pläne: {data.get('plans_total',0)}",
                f"Workflows: {data.get('workflows_total',0)}",
                f"Background Agents: {data.get('background_agents_total',0)} "
                f"({data.get('background_agents_active',0)} aktiv)"]
    return [str(data)]


def format_plan_explain_text(explain: dict[str, Any]) -> str:
    if not explain.get("ok"):
        return f"Explain nicht verfügbar: {explain.get('error') or explain.get('status') or 'unknown'}"

    lines = [
        f"Plan: {explain.get('plan_id','')}",
        f"Ziel: {explain.get('goal','')}",
        f"Status: {explain.get('status','')}",
        f"Maximum Risk: {explain.get('maximum_risk','low')}",
        f"Steps: {explain.get('step_count', 0)}",
        f"Approval Gates: {', '.join(explain.get('approval_gates', []) or ['-'])}",
        f"Risky Steps: {', '.join(explain.get('risky_steps', []) or ['-'])}",
        "",
        "Steps:",
    ]

    dependencies = explain.get("dependencies") or {}
    tool_mapping = explain.get("tool_mapping") or {}
    for step in explain.get("steps", []):
        step_id = str(step.get("id", ""))
        deps = dependencies.get(step_id) or step.get("dependencies") or []
        mapping = tool_mapping.get(step_id) or step.get("tool_mapping") or {}
        mapping_text = ", ".join(f"{k}={v}" for k, v in mapping.items()) if mapping else "-"
        lines.append(
            f"- {step_id}: [{step.get('status','')}] risk={step.get('risk_level','low')} "
            f"approval={step.get('requires_approval', False)}"
        )
        lines.append(f"  action={step.get('action','')}  tool={step.get('tool_name','') or '-'}")
        lines.append(f"  deps={', '.join(deps) if deps else '-'}")
        lines.append(f"  recovery={step.get('recovery_suggestion') or '-'}")
        lines.append(f"  tool_mapping={mapping_text}")

    audit = explain.get("audit") or []
    lines.extend(["", "Audit (latest 10):"])
    for row in audit[:10]:
        lines.append(f"- {row.get('ts','')}  {row.get('event','')}  {row.get('plan_id','')}")
    if not audit:
        lines.append("- keine Audit-Events")

    return "\n".join(lines)


def format_plan_explain_markdown(explain: dict[str, Any]) -> str:
    if not explain.get("ok"):
        return f"# Plan Explain\n\nNicht verfügbar: {explain.get('error') or explain.get('status') or 'unknown'}\n"

    plan_id = explain.get("plan_id", "")
    lines = [
        "# Plan Explain",
        "",
        f"- Plan: {plan_id}",
        f"- Ziel: {explain.get('goal','')}",
        f"- Status: {explain.get('status','')}",
        f"- Maximum Risk: {explain.get('maximum_risk','low')}",
        f"- Steps: {explain.get('step_count', 0)}",
        f"- Approval Gates: {', '.join(explain.get('approval_gates', []) or ['-'])}",
        f"- Risky Steps: {', '.join(explain.get('risky_steps', []) or ['-'])}",
        "",
        "## Steps",
    ]

    dependencies = explain.get("dependencies") or {}
    tool_mapping = explain.get("tool_mapping") or {}
    for step in explain.get("steps", []):
        step_id = str(step.get("id", ""))
        deps = dependencies.get(step_id) or step.get("dependencies") or []
        mapping = tool_mapping.get(step_id) or step.get("tool_mapping") or {}
        mapping_text = ", ".join(f"{k}={v}" for k, v in mapping.items()) if mapping else "-"
        lines.extend(
            [
                f"### {step_id}",
                f"- Status: {step.get('status','')}",
                f"- Risk: {step.get('risk_level','low')}",
                f"- Approval: {step.get('requires_approval', False)}",
                f"- Action: {step.get('action','')}",
                f"- Tool: {step.get('tool_name','') or '-'}",
                f"- Dependencies: {', '.join(deps) if deps else '-'}",
                f"- Recovery: {step.get('recovery_suggestion') or '-'}",
                f"- Tool Mapping: {mapping_text}",
                "",
            ]
        )

    lines.append("## Audit (latest 10)")
    audit = explain.get("audit") or []
    if not audit:
        lines.append("- keine Audit-Events")
    else:
        for row in audit[:10]:
            lines.append(f"- {row.get('ts','')}  {row.get('event','')}  {row.get('plan_id','')}")
    lines.append("")
    return "\n".join(lines)


def export_plan_explain(explain: dict[str, Any], project_root: str | Path, fmt: str) -> Path:
    root = Path(project_root)
    export_dir = root / "runtime" / "native" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    plan_id = str(explain.get("plan_id", "plan")).replace("/", "_").replace("\\", "_").replace(" ", "_")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fmt = fmt.lower().strip()
    if fmt == "json":
        out = export_dir / f"plan_explain_{plan_id}_{ts}.json"
        out.write_text(json.dumps(explain, ensure_ascii=False, indent=2), encoding="utf-8")
        return out
    if fmt == "md":
        out = export_dir / f"plan_explain_{plan_id}_{ts}.md"
        out.write_text(format_plan_explain_markdown(explain), encoding="utf-8")
        return out
    raise ValueError(f"unsupported_export_format:{fmt}")


def open_export_folder(project_root: str | Path, opener=None) -> Path:
    root = Path(project_root)
    export_dir = root / "runtime" / "native" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    if opener is not None:
        opener(export_dir)
        return export_dir
    if os.name == "nt":
        os.startfile(str(export_dir))  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(export_dir)])
    else:
        subprocess.Popen(["xdg-open", str(export_dir)])
    return export_dir


def build_panel(master, project_root: str | Path):
    import tkinter as tk
    from tkinter import ttk

    service = AgentControlService(project_root)
    frame = ttk.Frame(master, padding=4)
    notebook = ttk.Notebook(frame)
    notebook.pack(fill="both", expand=True)
    vm = service.view_model()
    for area in vm["areas"]:
        tab = {
            "id": area["id"],
            "title": area["title"],
            "ok": area["ok"],
            "lines": _area_lines(area["id"], area["data"]),
        }
        page = ttk.Frame(notebook)
        if tab["id"] == "plans" and area["data"].get("ok"):
            split = ttk.Panedwindow(page, orient="horizontal")
            left = ttk.Frame(split)
            right = ttk.Frame(split)
            split.add(left, weight=1)
            split.add(right, weight=2)
            split.pack(fill="both", expand=True)

            listbox = tk.Listbox(left)
            for line in tab["lines"]:
                listbox.insert("end", line)
            listbox.pack(fill="both", expand=True)

            explain_box = tk.Text(right, wrap="word")
            actions = ttk.Frame(right)
            actions.pack(fill="x")
            status_var = tk.StringVar(value="")
            status_label = ttk.Label(actions, textvariable=status_var)
            status_label.pack(side="right")
            explain_box.pack(fill="both", expand=True)

            plan_ids = [str(item.get("id", "")) for item in area["data"].get("plans", [])]
            current_explain: dict[str, Any] = {}

            def _set_explain(text: str) -> None:
                explain_box.configure(state="normal")
                explain_box.delete("1.0", "end")
                explain_box.insert("1.0", text)
                explain_box.configure(state="disabled")

            def _copy_explain() -> None:
                text = explain_box.get("1.0", "end-1c")
                if not text.strip():
                    status_var.set("Keine Explain-Daten zum Kopieren.")
                    return
                frame.clipboard_clear()
                frame.clipboard_append(text)
                status_var.set("Explain in Zwischenablage kopiert.")

            def _export(fmt: str) -> None:
                if not current_explain:
                    status_var.set("Kein Plan gewählt.")
                    return
                try:
                    out = export_plan_explain(current_explain, project_root, fmt)
                except Exception as exc:  # noqa: BLE001 - GUI must stay alive
                    status_var.set(f"Export fehlgeschlagen: {type(exc).__name__}")
                    _set_explain(f"Export Fehler: {exc}\n\n" + explain_box.get("1.0", "end-1c"))
                    return
                status_var.set(f"Exportiert: {out.name}")

            def _open_exports() -> None:
                try:
                    out_dir = open_export_folder(project_root)
                except Exception as exc:  # noqa: BLE001 - GUI must stay alive
                    status_var.set(f"Ordner öffnen fehlgeschlagen: {type(exc).__name__}")
                    _set_explain(f"Ordner-Fehler: {exc}\n\n" + explain_box.get("1.0", "end-1c"))
                    return
                status_var.set(f"Export-Ordner geöffnet: {out_dir.name}")

            ttk.Button(actions, text="Copy", command=_copy_explain).pack(side="left")
            ttk.Button(actions, text="Export MD", command=lambda: _export("md")).pack(side="left", padx=(6, 0))
            ttk.Button(actions, text="Export JSON", command=lambda: _export("json")).pack(side="left", padx=(6, 0))
            ttk.Button(actions, text="Open Export Folder", command=_open_exports).pack(side="left", padx=(6, 0))

            def _refresh_selected(*_):
                nonlocal current_explain
                selected = listbox.curselection()
                if not selected:
                    current_explain = {}
                    _set_explain("Plan auswählen, um Explain anzuzeigen.")
                    return
                idx = selected[0]
                if idx >= len(plan_ids):
                    current_explain = {}
                    _set_explain("Plan konnte nicht aufgelöst werden.")
                    return
                plan_id = plan_ids[idx]
                try:
                    explain = service.explain_plan(plan_id)
                except Exception as exc:  # noqa: BLE001 - GUI must stay alive
                    current_explain = {}
                    _set_explain(f"Explain Fehler für {plan_id}: {type(exc).__name__}: {exc}")
                    return
                current_explain = explain
                _set_explain(format_plan_explain_text(explain))

            listbox.bind("<<ListboxSelect>>", _refresh_selected)
            if plan_ids:
                listbox.selection_set(0)
                _refresh_selected()
            else:
                current_explain = {}
                _set_explain("Keine Pläne vorhanden.")
        else:
            listbox = tk.Listbox(page)
            for line in tab["lines"]:
                listbox.insert("end", line)
            listbox.pack(fill="both", expand=True)
        notebook.add(page, text=tab["title"])
    return frame


class AgentControlPanel:
    """Thin embeddable wrapper so the AI Workspace shell can host the surface."""

    def __init__(self, master, project_root: str | Path):
        self.frame = build_panel(master, project_root)

    def widget(self):
        return self.frame


def run_gui(project_root: str | Path = ".") -> int:
    try:
        import tkinter as tk
    except Exception as exc:  # pragma: no cover - headless
        print(f"tkinter_unavailable: {exc}")
        return 1
    root = tk.Tk()
    root.title("Agent Control Center")
    panel = AgentControlPanel(root, project_root)
    panel.widget().pack(fill="both", expand=True)
    root.mainloop()
    return 0
