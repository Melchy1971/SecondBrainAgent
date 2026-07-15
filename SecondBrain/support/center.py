"""Support Center orchestration: build the bundle, export a redacted ZIP and
render an HTML Support Center page. Artifacts land under
``OUTPUTS/v31.00-support-center/``.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from secondbrain.support.bundle import SupportBundle

__all__ = ["ARTIFACT_DIR", "run_support_center", "render_center_html", "write_artifacts"]

ARTIFACT_DIR = "OUTPUTS/v31.00-support-center"
ZIP_FILE = "support_bundle.zip"
JSON_FILE = "support_bundle.json"
HTML_FILE = "support_center.html"


def run_support_center(project_root: str | Path = ".", *, write: bool = True) -> dict[str, Any]:
    root = Path(project_root).resolve()
    sb = SupportBundle(root)
    bundle = sb.collect()
    if write:
        write_artifacts(root, sb, bundle)
    return bundle


def write_artifacts(project_root: str | Path, sb: SupportBundle, bundle: dict[str, Any]) -> dict[str, str]:
    directory = Path(project_root).resolve() / ARTIFACT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    zip_path = directory / ZIP_FILE
    sb.build_zip(zip_path, bundle=bundle)
    (directory / JSON_FILE).write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    (directory / HTML_FILE).write_text(render_center_html(bundle), encoding="utf-8")
    return {"zip": str(zip_path), "json": str(directory / JSON_FILE), "html": str(directory / HTML_FILE)}


def _summary(section: Any) -> str:
    if not isinstance(section, dict):
        return str(section)
    if section.get("ok") is False:
        return f"Fehler: {section.get('error', '')}"
    for key in ("status", "count", "configured", "psutil", "dialect"):
        if key in section:
            return f"{key}: {section[key]}"
    return "ok"


def render_center_html(bundle: dict[str, Any]) -> str:
    e = html.escape
    sections = bundle.get("sections", {})
    rows = []
    for name in sections:
        sec = sections[name]
        ok = not (isinstance(sec, dict) and sec.get("ok") is False)
        color = "#2fe6a0" if ok else "#ff5c5c"
        rows.append(
            f"<tr><td><b>{e(name)}</b></td>"
            f"<td><span style='color:{color}'>&#9679;</span> {e(_summary(sec))}</td>"
            f"<td><details><summary>anzeigen</summary><pre>{e(json.dumps(sec, ensure_ascii=False, indent=2)[:6000])}</pre></details></td></tr>"
        )
    return f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Support Center v31.00</title>
<style>
  body{{margin:0;background:#0a0e14;color:#d8ecf5;font:14px/1.5 system-ui,Segoe UI,Roboto,sans-serif}}
  .wrap{{max-width:1100px;margin:0 auto;padding:26px}}
  h1{{font-size:20px;letter-spacing:.04em;margin:0 0 4px}}
  .sub{{color:#7a93a6;margin-bottom:18px}}
  .note{{background:#111823;border:1px solid #1e2b3a;border-radius:10px;padding:12px 16px;margin-bottom:18px}}
  table{{width:100%;border-collapse:collapse;background:#0e141d;border:1px solid #1e2b3a;border-radius:10px;overflow:hidden}}
  th,td{{padding:10px 12px;text-align:left;border-bottom:1px solid #16202c;vertical-align:top}}
  th{{color:#8fb0c4;font-size:12px;text-transform:uppercase;letter-spacing:.06em;background:#0c1621}}
  pre{{white-space:pre-wrap;word-break:break-word;color:#9fb8c9;font-size:12px;max-height:320px;overflow:auto;margin:8px 0 0}}
  details summary{{cursor:pointer;color:#5ac8fa}}
</style></head>
<body><div class="wrap">
  <h1>SUPPORT CENTER &middot; v31.00</h1>
  <div class="sub">{e(bundle.get('generated_at',''))} &middot; {len(sections)} Sektionen</div>
  <div class="note">ZIP-Export: <b>support_bundle.zip</b> (im selben Ordner). Alle Inhalte sind <b>automatisch von Secrets bereinigt</b> ([REDACTED]).</div>
  <table>
    <thead><tr><th>Sektion</th><th>Status</th><th>Details</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</div></body></html>"""
