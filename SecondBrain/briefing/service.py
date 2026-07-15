"""Builder for consolidated daily and weekly briefings.

The builder aggregates already-fetched source data (calendar, tasks, mail,
projects, approvals, documents, reminders, system) into ordered sections. It
performs no I/O and triggers no external action - a briefing is read-only by
construction. Guarantees enforced here:

* every item keeps a source reference; items without solid backing are marked
  ``uncertain`` rather than dropped;
* secrets are redacted from every rendered string, including notification
  previews;
* a missing source becomes a ``connector_error`` section instead of a crash;
* an empty source yields an ``empty`` section, never a missing one;
* output is deterministic for identical input and ``now`` (reproducible);
* duplicates (same text + reference within a section) are collapsed.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

from secondbrain.briefing.models import (
    Briefing, BriefingItem, BriefingKind, BriefingSection, Priority, PRIORITY_WEIGHT, SectionStatus,
)

__all__ = ["BriefingBuilder", "redact_briefing_text", "DAILY_SECTIONS", "WEEKLY_SECTIONS"]

_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----[\s\S]*?-----END(?: [A-Z0-9]+)? PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----[\s\S]*", re.IGNORECASE),
    re.compile(r"(?i)[\w.\-]*(?:api[\s_-]?key|apikey|access[_-]?token|auth[_-]?token|token|secret|client[_-]?secret|password|passwd|credential(?:s)?)\s*[:=]\s*[^\s,;\"']+"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/-]+=*"),
    re.compile(r"sk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)
_REDACTED = "[REDACTED]"


def redact_briefing_text(text: str) -> str:
    out = text or ""
    for pattern in _SECRET_PATTERNS:
        out = pattern.sub(_REDACTED, out)
    return out


# section_id, title, source_key, bucket filter (None = all), base priority, order_rank
# order_rank realises: fixed appointments, deadlines, blocking tasks, approval
# deadlines, important communication, system errors. Lower rank == earlier.
DAILY_SECTIONS: tuple[tuple[str, str, str, str | None, str, int], ...] = (
    ("today_events", "Heutige Termine", "calendar", "today", Priority.HIGH.value, 1),
    ("meeting_prep", "Terminvorbereitung", "calendar", "prep", Priority.MEDIUM.value, 2),
    ("open_tasks", "Offene Aufgaben", "tasks", "open", Priority.MEDIUM.value, 6),
    ("overdue_tasks", "Überfällige Aufgaben", "tasks", "overdue", Priority.HIGH.value, 3),
    ("blocked_projects", "Blockierte Projekte", "projects", "blocked", Priority.HIGH.value, 4),
    ("important_mail", "Wichtige E-Mails", "mail", "important", Priority.MEDIUM.value, 7),
    ("follow_ups", "Follow-ups", "mail", "followup", Priority.MEDIUM.value, 8),
    ("open_approvals", "Offene Approvals", "approvals", None, Priority.HIGH.value, 5),
    ("connector_errors", "Connectorfehler", "system", "connector", Priority.HIGH.value, 9),
    ("relevant_documents", "Relevante Dokumente", "documents", None, Priority.LOW.value, 10),
    ("reminders", "Erinnerungen", "reminders", None, Priority.MEDIUM.value, 11),
    ("next_actions", "Empfohlene nächste Aktionen", "next_actions", None, Priority.MEDIUM.value, 12),
)

WEEKLY_SECTIONS: tuple[tuple[str, str, str, str | None, str, int], ...] = (
    ("top_goals", "Wichtigste Ziele", "goals", None, Priority.HIGH.value, 1),
    ("deadlines", "Deadlines", "deadlines", None, Priority.HIGH.value, 2),
    ("project_progress", "Projektfortschritt", "projects", "progress", Priority.MEDIUM.value, 5),
    ("conflicts", "Konflikte", "conflicts", None, Priority.HIGH.value, 3),
    ("risks", "Risiken", "risks", None, Priority.HIGH.value, 4),
    ("open_decisions", "Offene Entscheidungen", "decisions", None, Priority.HIGH.value, 6),
    ("completed_tasks", "Abgeschlossene Aufgaben", "tasks", "completed", Priority.LOW.value, 7),
    ("deferred_tasks", "Verschobene Aufgaben", "tasks", "deferred", Priority.MEDIUM.value, 8),
    ("week_review", "Wochenrückblick", "review", None, Priority.LOW.value, 9),
)


class BriefingBuilder:
    """Turns fetched source data into an ordered, deterministic briefing.

    ``sources`` maps a source key to one of:

    * ``None`` or absent -> connector missing (``connector_error`` section);
    * ``{"error": "..."}`` -> connector reachable but failing;
    * ``{"items": [ {text, source_reference, source?, confidence?, uncertain?,
      due?, preparation?, bucket?, kind?}, ... ]}`` -> data.
    """

    def __init__(self, *, hidden_references: Iterable[str] | None = None) -> None:
        self._hidden = {str(r) for r in (hidden_references or [])}

    # -- public API -------------------------------------------------------

    def build_daily(self, *, workspace_id: str, sources: Mapping[str, Any], now: datetime | None = None) -> Briefing:
        return self._build(BriefingKind.DAILY.value, DAILY_SECTIONS, workspace_id, sources, now)

    def build_weekly(self, *, workspace_id: str, sources: Mapping[str, Any], now: datetime | None = None) -> Briefing:
        return self._build(BriefingKind.WEEKLY.value, WEEKLY_SECTIONS, workspace_id, sources, now)

    def hide(self, source_reference: str) -> None:
        self._hidden.add(str(source_reference))

    def hide_in(self, briefing: Briefing, source_reference: str) -> int:
        """Mark every matching item hidden in an existing briefing. Returns count."""
        self._hidden.add(str(source_reference))
        count = 0
        for section in briefing.sections:
            for item in section.items:
                if item.source_reference == str(source_reference):
                    item.hidden = True
                    count += 1
        return count

    # -- rendering --------------------------------------------------------

    @staticmethod
    def to_json(briefing: Briefing) -> str:
        return json.dumps(briefing.to_dict(), ensure_ascii=False, sort_keys=True, indent=2)

    @staticmethod
    def to_markdown(briefing: Briefing) -> str:
        lines = [f"# Briefing ({briefing.kind}) – {briefing.generated_at}", ""]
        for section in briefing.sections:
            marker = "" if section.status == SectionStatus.OK.value else f" _({section.status})_"
            lines.append(f"## {section.title}{marker}")
            visible = section.visible_items
            if not visible:
                lines.append("_keine Einträge_")
            for item in visible:
                flag = " [unsicher]" if item.uncertain else ""
                due = f" (fällig: {item.due})" if item.due else ""
                lines.append(f"- {redact_briefing_text(item.text)}{due}{flag}")
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    @staticmethod
    def notification_preview(briefing: Briefing, *, max_lines: int = 5) -> list[str]:
        """Short, secret-free preview. No item bodies from private sources -
        only section titles and counts, plus critical approval headline."""
        preview: list[str] = []
        for section in briefing.sections:
            visible = section.visible_items
            if not visible:
                continue
            if section.priority == Priority.CRITICAL.value or section.section_id == "open_approvals":
                head = redact_briefing_text(visible[0].text)[:60]
                preview.append(f"{section.title}: {head}")
            else:
                preview.append(f"{section.title}: {len(visible)}")
            if len(preview) >= max_lines:
                break
        return preview

    # -- internals --------------------------------------------------------

    def _build(self, kind: str, specs: Sequence[tuple], workspace_id: str,
               sources: Mapping[str, Any], now: datetime | None) -> Briefing:
        moment = (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")
        sections: list[BriefingSection] = []
        for section_id, title, source_key, bucket, base_priority, order_rank in specs:
            section = self._section(section_id, title, source_key, bucket, base_priority,
                                    workspace_id, sources, moment)
            section._order_rank = order_rank  # type: ignore[attr-defined]
            sections.append(section)
        sections.sort(key=lambda s: (-PRIORITY_WEIGHT.get(s.priority, 0), getattr(s, "_order_rank", 99)))
        return Briefing(kind=kind, workspace_id=workspace_id, generated_at=moment, sections=sections)

    def _section(self, section_id: str, title: str, source_key: str, bucket: str | None,
                 base_priority: str, workspace_id: str, sources: Mapping[str, Any], moment: str) -> BriefingSection:
        raw = sources.get(source_key, "__missing__")
        if raw == "__missing__" or raw is None:
            return BriefingSection(section_id, title, base_priority, source_key, [], moment, 0.0,
                                   SectionStatus.CONNECTOR_ERROR.value)
        if isinstance(raw, Mapping) and raw.get("error"):
            return BriefingSection(section_id, title, base_priority, source_key, [], moment, 0.0,
                                   SectionStatus.CONNECTOR_ERROR.value)

        entries = raw.get("items", []) if isinstance(raw, Mapping) else list(raw)
        items = self._items(entries, bucket, source_key, workspace_id)
        if not items:
            return BriefingSection(section_id, title, base_priority, source_key, [], moment, 1.0,
                                   SectionStatus.EMPTY.value)

        priority = base_priority
        if any(i.kind == "critical" or i.due_is_critical for i in items):  # type: ignore[attr-defined]
            priority = Priority.CRITICAL.value
        confidence = round(sum(i.confidence for i in items) / len(items), 3)
        status = SectionStatus.UNCERTAIN.value if any(i.uncertain for i in items) else SectionStatus.OK.value
        return BriefingSection(section_id, title, priority, source_key, items, moment, confidence, status)

    def _items(self, entries: Sequence[Any], bucket: str | None, source_key: str, workspace_id: str) -> list[BriefingItem]:
        out: list[BriefingItem] = []
        seen: set[tuple[str, str]] = set()
        for entry in entries:
            if not isinstance(entry, Mapping):
                entry = {"text": str(entry)}
            if entry.get("workspace_id") not in (None, "", workspace_id):
                continue
            if bucket is not None and str(entry.get("bucket", "")) != bucket:
                continue
            ref = str(entry.get("source_reference", ""))
            if str(entry.get("hidden")) == "True" or ref in self._hidden:
                hidden = True
            else:
                hidden = False
            text = redact_briefing_text(str(entry.get("text", "")).strip())
            key = (re.sub(r"\s+", " ", text.lower()), ref)
            if key in seen:  # dedup within section
                continue
            seen.add(key)
            uncertain = bool(entry.get("uncertain")) or not ref
            item = BriefingItem(
                text=text,
                source_reference=ref,
                source=str(entry.get("source", source_key)),
                confidence=float(entry.get("confidence", 1.0)),
                uncertain=uncertain,
                hidden=hidden,
                kind=str(entry.get("kind", "")),
                due=str(entry.get("due", "")),
                preparation=[str(p) for p in entry.get("preparation", [])],
            )
            item.due_is_critical = bool(entry.get("critical"))  # type: ignore[attr-defined]
            out.append(item)
        out.sort(key=lambda i: (i.due or "~", i.text))  # deterministic
        return out
