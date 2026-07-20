from __future__ import annotations

from typing import Any, Mapping


def vault_status_labels(snapshot: Mapping[str, Any]) -> dict[str, str]:
    """Project a dashboard snapshot into bounded native status labels."""
    try:
        markdown_files = max(0, int(snapshot.get("markdown_files", 0)))
        inbox_files = max(0, int(snapshot.get("inbox_files", 0)))
    except (TypeError, ValueError):
        return {"markdown": "Unavailable", "vault": "Unknown", "inbox": "Unavailable"}
    vault_exists = snapshot.get("vault_exists")
    if not isinstance(vault_exists, bool):
        vault_label = "Unknown"
    else:
        vault_label = "Ready" if vault_exists else "Missing"
    return {
        "markdown": str(markdown_files),
        "vault": vault_label,
        "inbox": f"{inbox_files} Files",
    }
