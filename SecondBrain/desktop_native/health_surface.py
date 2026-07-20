from __future__ import annotations

from typing import Any, Mapping


def _check(bootstrap: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    checks = bootstrap.get("checks")
    if not isinstance(checks, list):
        return {}
    return next(
        (item for item in checks if isinstance(item, Mapping) and item.get("name") == name),
        {},
    )


def desktop_health_surface(bootstrap: Mapping[str, Any]) -> dict[str, str]:
    """Return allowlisted health labels without exposing configuration details."""
    database = _check(bootstrap, "database_url")
    database_detail = str(database.get("detail", ""))
    if not database:
        database_label = "Unknown"
    elif not bool(database.get("ok")):
        database_label = "Blocked"
    elif "PostgreSQL" in database_detail:
        database_label = "PostgreSQL"
    else:
        database_label = "Local fallback"

    env = bootstrap.get("env")
    provider = str(env.get("SECONDBRAIN_EMBEDDING_PROVIDER", "")).strip().lower() if isinstance(env, Mapping) else ""
    embeddings = _check(bootstrap, "embeddings")
    embedding_ok = bool(embeddings.get("ok"))
    provider_labels = {"local": "Local", "openai": "OpenAI", "ollama": "Ollama"}
    provider_label = provider_labels.get(provider, "Unknown")
    if not embeddings or provider_label == "Unknown":
        embedding_label = "Unknown"
    else:
        embedding_label = f"{provider_label} / {'Ready' if embedding_ok else 'Blocked'}"

    if provider != "ollama":
        ollama_label = "Not selected"
    elif not embeddings:
        ollama_label = "Unknown"
    else:
        ollama_label = "Reachable" if embedding_ok else "Offline"

    return {
        "database": database_label,
        "embedding": embedding_label,
        "ollama": ollama_label,
    }
