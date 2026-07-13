# v30.16 P1 Embedding HTTP Provider Boundary

## Ziel

Produktive Embedding-Provider dürfen nicht an einer optionalen SDK-Installation hängen und dürfen bei Fehlern nicht still auf lokale Testvektoren zurückfallen.

## Änderungen

- OpenAI Provider unterstützt jetzt native HTTPS-Calls gegen `/v1/embeddings`.
- OpenAI SDK bleibt kompatibel und wird genutzt, wenn vorhanden.
- Providerstatus zeigt `transport`: `sdk`, `http` oder `unavailable`.
- `SECONDBRAIN_EMBEDDING_TIMEOUT_SECONDS` steuert Provider-Timeouts.
- Timeout-Konfiguration wird an OpenAI und Ollama Provider propagiert.
- HTTP-/Netzwerkfehler bleiben harte Fehler, wenn Fallback nicht explizit erlaubt ist.

## Akzeptanz

```bash
pytest -q tests/test_v3016_p1_embedding_http_provider.py tests/test_v3015_p1_embedding_dimension_contract.py tests/test_v3014_p1_embedding_config_contract.py
```

Ergebnis im Delta-Build: `13 PASS`.

## Konsequenz

P1 ist näher an produktiver Semantic-RAG-Fähigkeit: Provider-Konfiguration, Dimension Contract und echte Transportpfade sind getrennt testbar. Offen bleiben Live-Provider-Health gegen echte Keys/Endpoints und Volltest außerhalb der Sandbox.
