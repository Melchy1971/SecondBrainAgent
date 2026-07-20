from secondbrain.desktop_native.health_surface import desktop_health_surface


def _bootstrap(*, database_detail: str, provider: str, embedding_ok: bool = True) -> dict:
    return {
        "checks": [
            {"name": "database_url", "ok": True, "detail": database_detail},
            {"name": "embeddings", "ok": embedding_ok, "detail": "sensitive runtime detail"},
        ],
        "env": {
            "SECONDBRAIN_EMBEDDING_PROVIDER": provider,
            "SECONDBRAIN_EMBEDDING_MODEL": "secret-model-name",
        },
    }


def test_local_fallback_and_local_embeddings_are_reported() -> None:
    result = desktop_health_surface(
        _bootstrap(database_detail="DATABASE_URL fehlt; lokaler Fallback", provider="local")
    )

    assert result == {
        "database": "Local fallback",
        "embedding": "Local / Ready",
        "ollama": "Not selected",
    }


def test_postgres_and_reachable_ollama_are_reported() -> None:
    result = desktop_health_surface(
        _bootstrap(database_detail="PostgreSQL DSN konfiguriert", provider="ollama")
    )

    assert result == {
        "database": "PostgreSQL",
        "embedding": "Ollama / Ready",
        "ollama": "Reachable",
    }


def test_failed_selected_ollama_is_offline_without_leaking_details() -> None:
    result = desktop_health_surface(
        _bootstrap(database_detail="PostgreSQL DSN konfiguriert", provider="ollama", embedding_ok=False)
    )

    assert result["embedding"] == "Ollama / Blocked"
    assert result["ollama"] == "Offline"
    assert "sensitive" not in str(result)
    assert "secret-model-name" not in str(result)


def test_missing_or_unknown_health_data_is_explicit() -> None:
    assert desktop_health_surface({}) == {
        "database": "Unknown",
        "embedding": "Unknown",
        "ollama": "Not selected",
    }
    assert desktop_health_surface(
        _bootstrap(database_detail="invalid", provider="custom")
    )["embedding"] == "Unknown"
