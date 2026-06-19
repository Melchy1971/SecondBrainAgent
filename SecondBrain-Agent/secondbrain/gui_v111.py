from __future__ import annotations

from pathlib import Path
from typing import Any
import json


def build_dashboard_model(runtime: Any) -> dict[str, Any]:
    status = runtime.status()
    metrics = runtime.metrics()
    services = status.get('services', {})
    return {
        'title': 'SecondBrain OS v11.1',
        'summary': {
            'services_running': metrics.get('services_running', 0),
            'services_total': metrics.get('services_total', 0),
            'services_error': metrics.get('services_error', 0),
            'runtime_bytes': metrics.get('runtime_bytes', 0),
        },
        'services': services,
        'session': status.get('session', {}),
    }


def write_dashboard_snapshot(runtime: Any, path: str | Path | None = None) -> Path:
    target = Path(path) if path else runtime.project_root / 'runtime' / 'dashboard_snapshot.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build_dashboard_model(runtime), ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    return target


def run_tk_dashboard(runtime: Any) -> int:
    """Minimal Tk dashboard. In headless environments it writes a snapshot instead."""
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
    except Exception:
        write_dashboard_snapshot(runtime)
        return 0

    try:
        root = tk.Tk()
    except Exception:
        write_dashboard_snapshot(runtime)
        return 0

    root.title('SecondBrain OS v11.1')
    root.geometry('780x520')

    header = ttk.Label(root, text='SecondBrain OS v11.1 Runtime Dashboard', font=('Segoe UI', 16, 'bold'))
    header.pack(padx=12, pady=10, anchor='w')

    summary_var = tk.StringVar()
    summary = ttk.Label(root, textvariable=summary_var)
    summary.pack(padx=12, pady=4, anchor='w')

    columns = ('service', 'status', 'checks', 'error')
    tree = ttk.Treeview(root, columns=columns, show='headings')
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=160 if col != 'error' else 280)
    tree.pack(fill='both', expand=True, padx=12, pady=8)

    button_frame = ttk.Frame(root)
    button_frame.pack(fill='x', padx=12, pady=8)

    def refresh():
        model = build_dashboard_model(runtime)
        s = model['summary']
        summary_var.set(f"Running: {s['services_running']}/{s['services_total']} | Errors: {s['services_error']} | Runtime bytes: {s['runtime_bytes']}")
        for item in tree.get_children():
            tree.delete(item)
        for name, state in model['services'].items():
            tree.insert('', 'end', values=(name, state.get('status'), state.get('checks'), state.get('last_error', '')))

    def start_runtime():
        runtime.start()
        refresh()

    def stop_runtime():
        runtime.stop()
        refresh()

    def diagnose():
        result = runtime.diagnose()
        refresh()
        messagebox.showinfo('Diagnostics', json.dumps({'status': result['status'], 'metrics': result['metrics']}, ensure_ascii=False, indent=2))

    ttk.Button(button_frame, text='Start', command=start_runtime).pack(side='left', padx=4)
    ttk.Button(button_frame, text='Stop', command=stop_runtime).pack(side='left', padx=4)
    ttk.Button(button_frame, text='Diagnose', command=diagnose).pack(side='left', padx=4)
    ttk.Button(button_frame, text='Refresh', command=refresh).pack(side='left', padx=4)

    refresh()
    root.mainloop()
    return 0
