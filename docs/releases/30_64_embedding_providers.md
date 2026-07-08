# v30.64 — Produktive Embedding-Provider mit Safety-Gates

## Analyse
Bestehend: `p1_embeddings.py` (Local/Ollama/OpenAI mit gated Fallback) + ein zweiter Stack unter
`rag/providers/` inkl. `DeterministicEmbeddingProvider` (Fake). Beide bleiben unangetastet. Neu ist ein
konsolidiertes `secondbrain/embeddings/`-Paket mit injizierbarem HTTP-Transport (offline testbar).

## Zwei harte Regeln (erstklassig + getestet)
1. **Kein stiller Fake:** Netzwerk-Provider werfen bei Fehlern (`EmbeddingProviderError`/`OfflineError`/
   `DimensionMismatchError`) statt Fake-Vektoren zurueckzugeben. Die Factory verweigert `local` ausser
   bei explizitem `allow_local`/`SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK=1` (nur Development).
2. **Gate FAIL bei Fehler:** `embedding_production_gate` liefert FAIL bei Health!=PASS und bei
   nicht-produktivem Provider (local/fake in production). Ein Fake bekommt in Produktion NIE PASS.

## Neu
- `providers.py` — `OpenAIEmbeddingProvider`, `OllamaEmbeddingProvider`, `LocalEmbeddingProvider`
  (deterministisch, `production_ready=False`). Batch-Requests, Dimension-Enforcement, injizierbarer Transport.
- `health.py`/`ProviderHealth` — Health-Probe mit PASS/FAIL.
- `validation.py` — Dimension- + Model-Validierung.
- `cache.py` — content-adressierter `EmbeddingCache` + `CachingEmbeddingProvider`.
- `batch.py` — `embed_batch_chunked` mit **Retry + Backoff** (reuse `storage.db_retry`).
- `offline.py` — Offline-Detection.
- `factory.py` — `build_provider` (nie still Fake).
- `gate.py` — Production-Gate.
- `reindex.py` — **Automatic Reindex** bei Provider-Identity-Change (`provider:model:dim`) via vector_store.reindex.

## Launcher (Python 3.11+)
```
python launcher.py embed-health   --provider openai --model text-embedding-3-small --dimensions 1536
python launcher.py embed-validate --provider ollama --model nomic-embed-text --dimensions 768
python launcher.py embed-gate     --environment production      # Exit 4 bei FAIL
```

## Tests
`tests/embeddings/` (17 passed, 1 skipped): Provider (OpenAI/Ollama via FakeTransport, Dim-Mismatch,
401/503, **fehlender API-Key -> Fehler statt Fake**), Cache (kein Recompute), Batch (Retry auf transient),
Validation, Offline, **Safety** (Factory nie Fake fuer openai; Gate FAIL bei Fehler/local-in-prod; Reindex
bei Identity-Change). Live OpenAI-Test nur mit `OPENAI_API_KEY`, sonst skip.

## Grenzen
Sandbox ohne echte OpenAI/Ollama-Endpunkte -> Netz-Provider offline via FakeTransport getestet; echte
Vektorqualitaet/Latenz nur am Live-System. Ollama-Batch ist per-Text (loop); `/api/embed`-Batch koennte
spaeter ergaenzt werden.
