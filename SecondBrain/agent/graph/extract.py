"""v30.72 Knowledge Graph - extraction from existing Memory records.

Derives entities, people, projects, relations and dates from what memory records
already carry (tags + metadata). Conventions - all optional, all read from
existing data (no new storage):

* typed tags: ``person:Markus``, ``project:SAP``, ``entity:Telekom``
* plain tags: treated as generic ``entity`` nodes
* metadata lists: ``people``, ``projects``, ``entities``
* metadata relations: ``relations = [{"subject","relation","object"}]``
* ``created_at`` drives the timeline
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .models import N_ENTITY, N_PERSON, N_PROJECT

_TAG_TYPE = {"person": N_PERSON, "people": N_PERSON, "project": N_PROJECT,
             "entity": N_ENTITY, "org": N_ENTITY, "organisation": N_ENTITY}
_META_TYPE = {"people": N_PERSON, "persons": N_PERSON, "projects": N_PROJECT,
              "entities": N_ENTITY, "orgs": N_ENTITY}


def _get(record: Any, attr: str, default: Any) -> Any:
    return getattr(record, attr, default)


def node_id(node_type: str, value: str) -> str:
    return f"{node_type}:{value.strip()}"


def entities_of(record: Any) -> list[tuple[str, str]]:
    """Return (node_type, value) pairs mentioned by a record."""
    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def emit(node_type: str, value: str) -> None:
        value = (value or "").strip()
        if not value:
            return
        pair = (node_type, value)
        if pair not in seen:
            seen.add(pair)
            out.append(pair)

    for tag in _get(record, "tags", ()) or ():
        tag = str(tag)
        if ":" in tag:
            prefix, _, value = tag.partition(":")
            emit(_TAG_TYPE.get(prefix.lower(), N_ENTITY), value)
        else:
            emit(N_ENTITY, tag)

    metadata = _get(record, "metadata", {}) or {}
    for key, node_type in _META_TYPE.items():
        values = metadata.get(key)
        if isinstance(values, (list, tuple)):
            for v in values:
                emit(node_type, str(v))
        elif isinstance(values, str) and values:
            emit(node_type, values)
    return out


def relations_of(record: Any) -> list[tuple[str, str, str]]:
    metadata = _get(record, "metadata", {}) or {}
    rels = metadata.get("relations")
    out: list[tuple[str, str, str]] = []
    if isinstance(rels, (list, tuple)):
        for r in rels:
            if isinstance(r, dict) and r.get("subject") and r.get("object"):
                out.append((str(r["subject"]), str(r.get("relation", "related_to")), str(r["object"])))
    return out


def date_of(record: Any) -> str:
    created = _get(record, "created_at", None)
    if isinstance(created, datetime):
        return created.date().isoformat()
    metadata = _get(record, "metadata", {}) or {}
    if metadata.get("date"):
        return str(metadata["date"])[:10]
    return ""


def project_of(record: Any) -> str | None:
    """Best-effort project context: explicit project entity or workspace_id."""
    for node_type, value in entities_of(record):
        if node_type == N_PROJECT:
            return value
    ws = _get(record, "workspace_id", None)
    return ws if ws and ws not in ("shared",) else None


def label_of(record: Any) -> str:
    text = str(_get(record, "text", "") or "")
    return text[:60] + ("…" if len(text) > 60 else "")
