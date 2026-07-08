# Embedding-Provider: Ist-Analyse und Härtung des Alt-Stacks

Stand: 2026-07-08. Scope laut Freigabe: Analyse aller Embedding-Provider plus
Härtung des Alt-Stacks `secondbrain/rag/providers/`. Kein Umbau der beiden
anderen Stacks.

## 1. Befund: drei parallele Embedding-Ebenen

Im Repo existieren drei voneinander unabhängige Embedding-Implementierungen.

| Ebene | Pfad | Interface | Rolle | Silent-Fallback-Risiko (vor Härtung) |
|------|------|-----------|-------|--------------------------------------|
| A | `secondbrain/embeddings/` (v30.64) | `health() -> ProviderHealth` | Saubere Referenz-Schicht | nein |
| B | `secondbrain/p1_embeddings.py` + `p1_*` | `status() -> dict` | Tatsächlicher Production-Gate-Pfad | nein (Fallback nur per Env-Flag, Gate blockt) |
| C | `secondbrain/rag/providers/` | `embed(texts)` | RAG-Adapter/Library | ja |

Aufrufer-Realität (verifiziert per Grep):

- Ebene B wird über `provider_from_profile()` in den p1-Gate gehängt und ist der
  produktive Pfad. `p1_provider_health.evaluate_embedding_provider_health()`
  blockt `local`/`deterministic` in Production, blockt bei fehlgeschlagener Probe
  und bei `fallback_used`.
- Ebene A wird ausschließlich von den eigenen Tests unter `tests/embeddings/`
  genutzt. Vollständig, aber nicht verdrahtet.
- Ebene C (`EmbeddingFactory`, `DeterministicEmbeddingProvider`) hatte **keinen**
  Runtime-Aufrufer außerhalb der Tests. Regressionsarm zu härten, aber als
  öffentliche API ein latentes Risiko: wer sie verdrahtet, bekommt ohne
  Gegenmaßnahme stille Fake-Embeddings.

## 2. Abgleich gegen die Akzeptanzkriterien

| Kriterium | Ebene A | Ebene B (Prod-Gate) | Ebene C vorher | Ebene C nachher |
|-----------|---------|---------------------|----------------|-----------------|
| Kein stiller Fake/Fallback | erfüllt | erfüllt | verletzt | erfüllt |
| OpenAI live validieren | health() | status() Live-Probe | nur embed | health() Live-Probe |
| Ollama live validieren | health() | status() Live-Probe | nur embed | health() Live-Probe |
| Lokaler Provider = DEV_ONLY | production_ready=False | production_ready=False | nicht markiert | dev_only=True |
| Dimension-Validation | ja | ja (enforce_dimensions) | nur normalize_vectors | validate_dimensions + enforce |
| Model-Validation | validate_model | KNOWN/PRODUCTION_PROVIDERS | fehlt | validate_model |
| Provider-Health-Report | ProviderHealth | status()-dict + p1-Report | fehlt | ProviderHealthReport |
| Reindex-Flag bei Wechsel | provider_identity | embedding_index_provider | fehlt | provider_index_identity + reindex_required |
| Gate blockt DEV_ONLY | embedding_production_gate | p1_provider_health | fehlt | embedding_production_gate |

Kernaussage: Der Production-Gate-Pfad (Ebene B) erfüllt die Kriterien bereits.
Die einzige echte Lücke war Ebene C.

## 3. Konkretes Risiko im Alt-Stack (vor Härtung)

1. `DeterministicEmbeddingProvider` war dokumentiert als "safe offline fallback
   ... degraded operation when real embedding services are unavailable". Dieses
   Framing legitimiert stille Fakes im Betrieb.
2. `EmbeddingFactory.create()` ohne Argumente lieferte defaultmäßig
   `deterministic` — ein stiller Fake als Standard.
3. `create()` mappte `local`/`offline`/`hash` -> deterministic, ohne Gate.
4. Kein `health()`, kein `production_ready`, keine DEV_ONLY-Markierung, keine
   Dimension-/Model-Enforcement-Option, keine Reindex-Identität.

## 4. Durchgeführte Härtung (Ebene C)

Dateien unter `secondbrain/rag/providers/`:

- `base.py`: Fehlerklassen `ProviderOfflineError`, `DimensionMismatchError`,
  `ModelNotAllowedError`; `ProviderHealthReport`; Helfer `validate_dimensions`,
  `validate_model`, `provider_index_identity`, `reindex_required`.
- `deterministic_provider.py`: DEV_ONLY (`dev_only=True`,
  `production_ready=False`, `semantic=False`), `health()`, Docstring ohne
  Fallback-Framing.
- `openai_embedding_provider.py`, `ollama_embedding_provider.py`:
  semantic/production_ready-Flags, optionaler Dimension-Contract
  (`enforce_dimensions`), Live-`health()` das bei Offline FAIL liefert statt
  Fake. `embed()` wirft weiter über die HTTP-Clients — kein Fallback.
- `gemini_provider.py`: Flags + `health()`.
- `factory.py`: fail-closed. `create()` ohne expliziten Provider wirft.
  DEV_ONLY in Production geblockt, außer `allow_dev_only=True` bzw.
  `SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK=1`. Dimension-Durchreichung.
- `health.py` (neu): `provider_health()`, `embedding_production_gate()`. Blockt
  fehlgeschlagene Proben, DEV_ONLY und nicht-produktionsreife Provider;
  unbekannte Provider ohne `health()` gelten als FAIL.
- `__init__.py`: Re-Exports.

Env-Flag `SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK` identisch zu Ebene B, damit die
Dev-Freigabe über alle Stacks eine einzige Schraube ist.

## 5. Testabdeckung

`tests/rag/providers/test_hardening.py`, 18 Fälle: deterministic DEV_ONLY + Gate;
Factory fail-closed; OpenAI/Ollama offline = FAIL ohne Fake; Dimension-Mismatch;
Model-Validation; Reindex-Identität/Flag; unbekannter Provider = FAIL.

Gesamtlauf (Sandbox, Python 3.10, pytest-tmp auf lokalem FS):
60 passed, 1 skipped (Live-OpenAI ohne API-Key). Bestehende Tests bleiben grün.
Lint (`ruff check`) sauber.

Umgebungshinweis: Die p1-/launcher-Tests importieren `datetime.UTC` und laufen
nur unter Python >= 3.11. Der Sandbox-Interpreter ist 3.10; diese Suiten wurden
nicht ausgeführt. Die Härtung berührt Ebene B nicht. Abnahme dennoch erst nach
3.11-Lauf auf deinem System.

## 6. Offener Punkt (nicht Teil dieses Auftrags)

Drei Embedding-Stacks mit drei Interfaces sind langfristig ein Wartungsrisiko und
eine Quelle für Gate-Lücken. Empfehlung Folge-Arbeitspaket: Ebene A als
kanonische Schicht festlegen, Ebene B darauf umstellen, Ebene C auf A umbiegen
oder deprecaten. Bewusst nicht hier umgesetzt, da es Ebene B verändert und ein
eigenes Regressionsbudget braucht.
