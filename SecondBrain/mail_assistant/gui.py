"""Mail assistant GUI view model and headless HTML renderer.

The view model never exposes technical identifiers in list/overview data; only
detail payloads carry a source reference so a user can open the underlying
message. Nothing here sends mail - write actions are surfaced as approval
links that the approval inbox owns.
"""

from __future__ import annotations

import html
from typing import Any, Sequence

from secondbrain.mail_assistant.models import MailMessage, MailThread
from secondbrain.mail_assistant.service import MailAssistant

__all__ = ["MailViewModel", "render_mail_html"]


class MailViewModel:
    def __init__(self, assistant: MailAssistant) -> None:
        self.assistant = assistant

    def build(self, *, workspace_id: str, messages: Sequence[MailMessage],
              threads: Sequence[MailThread], thread_messages: dict[str, Sequence[MailMessage]] | None = None) -> dict[str, Any]:
        tmsgs = thread_messages or {}
        prioritized = self.assistant.prioritize_inbox(messages, workspace_id=workspace_id)
        thread_views = []
        drafts = []
        follow_ups = []
        tasks = []
        for t in self.assistant.list_threads(threads, workspace_id=workspace_id):
            msgs = tmsgs.get(t.thread_id, [])
            summary = self.assistant.summarize_thread(msgs) if msgs else {"summary": t.summary, "open_questions": [], "attachments": []}
            thread_views.append({"subject": t.subject, "participants": t.participants,
                                 "category": t.category, "summary": summary["summary"],
                                 "unread_count": t.unread_count})
            if msgs:
                fu = self.assistant.detect_follow_up(msgs)
                if fu.get("follow_up"):
                    follow_ups.append({"subject": t.subject, "reason": fu.get("reason", "")})
                drafts.append({"subject": t.subject, **self.assistant.generate_reply_draft(msgs)})
        for m in self.assistant.list_messages(messages, workspace_id=workspace_id):
            tasks.extend(self.assistant.extract_tasks(m))
        return {
            "workspace_id": workspace_id,
            "prioritized_inbox": [self._public(p) for p in prioritized],
            "threads": thread_views,
            "drafts": drafts,
            "follow_ups": follow_ups,
            "tasks_from_mail": tasks,
            "approval_actions": [{"label": "Freigabe öffnen", "target": "approval_inbox"}],
        }

    @staticmethod
    def _public(row: dict[str, Any]) -> dict[str, Any]:
        # keep source_reference for detail open, drop nothing else technical
        return {k: v for k, v in row.items() if k not in ("factors",)} | {"factors": row.get("factors", {})}


def render_mail_html(view: dict[str, Any]) -> str:
    def esc(value: Any) -> str:
        return html.escape(str(value))

    rows = "".join(
        f"<tr><td>{esc(p['subject'])}</td><td>{esc(p['sender'])}</td>"
        f"<td>{esc(p['category'])}</td><td class='score'>{esc(round(p['score'], 2))}</td></tr>"
        for p in view["prioritized_inbox"]
    )
    threads = "".join(
        f"<div class='thread'><h4>{esc(t['subject'])} <span class='cat'>{esc(t['category'])}</span></h4>"
        f"<p>{esc(t['summary'])}</p></div>"
        for t in view["threads"]
    )
    drafts = "".join(
        f"<div class='draft'><h4>{esc(d['subject'])}</h4><pre>{esc(d['draft'])}</pre>"
        f"<small>{esc(d['disclaimer'])}</small></div>"
        for d in view["drafts"]
    )
    follow = "".join(f"<li>{esc(f['subject'])} – {esc(f['reason'])}</li>" for f in view["follow_ups"])
    tasks = "".join(
        f"<li>{esc(tk['candidate_title'])} <em>({esc(tk['confidence'])})</em></li>"
        for tk in view["tasks_from_mail"]
    )
    return f"""<!doctype html><html lang='de'><head><meta charset='utf-8'>
<title>E-Mail-Assistent</title><style>
body{{font-family:system-ui,Segoe UI,sans-serif;margin:24px;color:#111;background:#f7f7f9}}
h2{{border-bottom:2px solid #e20074;padding-bottom:4px}}
table{{border-collapse:collapse;width:100%;background:#fff}}
td,th{{border:1px solid #ddd;padding:6px 8px;text-align:left}}
.score{{font-weight:700;color:#e20074}}
.thread,.draft{{background:#fff;border:1px solid #e3e3e3;border-radius:8px;padding:10px;margin:8px 0}}
.cat{{font-size:12px;color:#666}}
pre{{white-space:pre-wrap;background:#fafafa;padding:8px;border-radius:6px}}
</style></head><body>
<h1>E-Mail-Assistent</h1>
<h2>Priorisierter Posteingang</h2>
<table><thead><tr><th>Betreff</th><th>Absender</th><th>Kategorie</th><th>Score</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Threads &amp; Zusammenfassung</h2>{threads}
<h2>Antwort-Entwürfe (nicht gesendet)</h2>{drafts}
<h2>Follow-ups</h2><ul>{follow}</ul>
<h2>Aufgaben aus E-Mail</h2><ul>{tasks}</ul>
<h2>Freigaben</h2><p><a href='#approval_inbox'>Freigabe öffnen</a></p>
</body></html>"""
