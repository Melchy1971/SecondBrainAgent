from secondbrain.desktop_native.alert_surface import live_alert_labels


def test_configured_postgres_and_queue_counts_are_projected() -> None:
    result = live_alert_labels(
        health={"database": "PostgreSQL", "embedding": "Ollama / Ready", "ollama": "Reachable"},
        jobs={"counts": {"pending": 2, "retry": 1, "blocked": 4, "success": 99}},
    )

    assert result == {
        "embedding": "Ollama / Ready",
        "postgresql": "Configured",
        "pgvector": "Not checked",
        "ollama": "Reachable",
        "queue": "3 Pending / 4 Blocked",
    }


def test_local_fallback_and_empty_queue_are_explicit() -> None:
    result = live_alert_labels(
        health={"database": "Local fallback", "embedding": "Local / Ready", "ollama": "Not selected"},
        jobs={"counts": {}},
    )

    assert result["postgresql"] == "Not selected"
    assert result["queue"] == "0 Pending"


def test_invalid_counts_and_unknown_health_degrade_safely() -> None:
    result = live_alert_labels(
        health={"database": "postgresql://user:secret@host/db"},
        jobs={"counts": {"pending": "invalid", "retry": -2, "blocked": None}},
    )

    assert result == {
        "embedding": "Unknown",
        "postgresql": "Unknown",
        "pgvector": "Not checked",
        "ollama": "Unknown",
        "queue": "0 Pending",
    }
    assert "secret" not in str(result)
