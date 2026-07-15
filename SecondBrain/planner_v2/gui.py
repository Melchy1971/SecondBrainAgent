"""Planner GUI view model and headless HTML renderer.

Shows the plan graph as ordered layers, per-node risk and approval flags, the
simulation summary, validation issues and the run status. Node objectives and
tools are shown; the technical plan_id is kept in the detail payload only.
"""

from __future__ import annotations

import html
from typing import Any

from secondbrain.planner_v2.models import PlanGraph
from secondbrain.planner_v2.service import Planner

__all__ = ["PlannerViewModel", "render_plan_html"]


class PlannerViewModel:
    def __init__(self, planner: Planner) -> None:
        self.planner = planner

    def build(self, plan: PlanGraph) -> dict[str, Any]:
        issues = self.planner.validate_plan(plan)
        sim = self.planner.simulate_plan(plan)
        layers = []
        for idx, layer in enumerate(self.planner.execution_layers(plan)):
            layers.append({"index": idx, "nodes": [self._node(plan, nid) for nid in layer]})
        return {
            "goal": plan.goal,
            "status": plan.status,
            "layers": layers,
            "parallel_groups": self.planner.parallel_groups(plan),
            "issues": issues,
            "simulation": sim,
            "approvals": sim["approvals"],
            "audit": plan.audit,
        }

    @staticmethod
    def _node(plan: PlanGraph, node_id: str) -> dict[str, Any]:
        n = plan.node(node_id)
        return {"objective": n.objective, "tool": n.tool, "risk": n.risk,
                "approval_required": n.approval_required, "status": n.status,
                "cost": n.estimated_cost}


def render_plan_html(view: dict[str, Any]) -> str:
    def esc(v: Any) -> str:
        return html.escape(str(v))

    layers = []
    for layer in view["layers"]:
        nodes = "".join(
            f"<li>{esc(n['objective'])} <code>{esc(n['tool'])}</code>"
            f"<span class='r r-{esc(n['risk'])}'>{esc(n['risk'])}</span>"
            f"{' 🔒Approval' if n['approval_required'] else ''}</li>"
            for n in layer["nodes"])
        layers.append(f"<div class='layer'><h3>Ebene {esc(layer['index'])} (parallel)</h3><ul>{nodes}</ul></div>")
    issues = "".join(f"<li>{esc(i['type'])}: {esc(i.get('detail',''))}</li>" for i in view["issues"]) or "<li>keine</li>"
    sim = view["simulation"]
    return f"""<!doctype html><html lang='de'><head><meta charset='utf-8'>
<title>Planner V2</title><style>
body{{font-family:system-ui,Segoe UI,sans-serif;margin:24px;color:#111;background:#f6f6f8}}
h1,h2{{color:#e20074}}
.layer{{background:#fff;border:1px solid #e2e2e2;border-radius:8px;padding:8px 14px;margin:8px 0}}
code{{background:#eef;padding:1px 5px;border-radius:4px;margin:0 6px}}
.r{{font-size:11px;padding:1px 6px;border-radius:10px;margin-left:6px}}
.r-high,.r-critical{{background:#fde2e2;color:#c0142c}}
.r-low,.r-medium{{background:#eef7e2;color:#3a6d00}}
ul{{padding-left:18px}}
</style></head><body>
<h1>Planner V2</h1>
<p><b>Ziel:</b> {esc(view['goal'])} · Status: {esc(view['status'])}</p>
<p>Simulation: {len(sim['planned_actions'])} Schritte · Kosten {esc(sim['estimated_cost'])} · Dauer {esc(sim['estimated_duration'])} · Approvals {len(sim['approvals'])} · ausgeführt: {esc(sim['executed'])}</p>
<h2>Ausführungsebenen</h2>{"".join(layers)}
<h2>Validierung</h2><ul>{issues}</ul>
</body></html>"""
