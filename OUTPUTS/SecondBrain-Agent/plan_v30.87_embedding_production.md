# Plan: v30.87 — Embedding Provider produktionsreif machen

Branch: `feature/v30.87-embedding-production`
Commit (final): `fix(embeddings): enforce production provider readiness`
Repo: https://github.com/Melchy1971/SecondBrainAgent.git (lokal `h:\SecondBrainAgent`, `main` sauber)

---

## Phase 0 — Documentation Discovery (abgeschlossen)

### Kernbefund: drei parallele Embedding-Stacks

Das Repo enthält **drei unabhängige EmbeddingProvider-Implementierungen**, die dieselben Regeln unterschiedlich (und teils widersprüchlich) umsetzen:

| Stack | Ort | Contract | Genutzt von |
|---|---|---|---|
| A | `secondbrain/embeddings/` (`base.py`, `providers.py`, `factory.py`, `gate.py`, `reindex.py`) | `embed(text)`/`embed_batch`, `.health()` → `ProviderHealth` | `launcher.py` Commands `embed-health/embed-validate/embed-gate` — isoliert, nicht am realen Production Gate |
| **B (Ziel dieses Plans)** | `secondbrain/p1_embeddings.py`, `p1_embedding_config.py`, `p1_provider_health.py`, `p1_production_gate.py`, `p1_vector_provider_guard.py` | `embed(text)`, `.status()` → `dict` | `P1RagRuntime`, Launcher-Commands `p1-provider-health`, `p1-production`, `p1-embedding-config`, `p1-vector-provider-audit` — **das ist der tatsächlich scharfgeschaltete Production Gate** |
| C | `secondbrain/rag/providers/` (`base.py`, `factory.py`, `health.py`, `*_provider.py`) | `embed(texts: list)` (batch-first), `.health()` → `ProviderHealthReport`, `dev_only: bool` | RAG-Pipeline-Batch-Pfad, separat |

**Entscheidung:** Stack B wird gehärtet. Begründung:
1. Es ist der Stack, der tatsächlich in `launcher.py` an `p1-production` (den einzigen produktiv exerzierten Gate-Command) hängt.
2. Die vom Auftrag vorgegebenen Testdateinamen (`tests/test_p1_production_gate.py` etc.) folgen der `p1_`-Namenskonvention dieses Stacks.
3. Stack B enthält aktuell genau das Anti-Pattern, das der Auftrag verbietet (siehe unten) — das ist der eigentliche Härtungsbedarf.

Stack A/C werden **nicht** angefasst (kein Duplikat-Umbau, kein Scope-Creep).

### 1. Vorhandene EmbeddingProvider (Stack B)

`secondbrain/p1_embeddings.py`:
- `LocalEmbeddingProvider` (Z. 85-107, `@dataclass(frozen=True)`) — `name="local-deterministic"`, `embed()`, `status()` liefert bereits `"production_ready": False`.
- `OllamaEmbeddingProvider` (Z. 110-182) — `embed()` (Z. 134-140), `status()` (Z. 142-182), Requests via `urllib.request` an `{base_url}/api/embeddings`.
- `OpenAIEmbeddingProvider` (Z. 185-324) — `embed()` (Z. 273-279), `status()` (Z. 281-324), SDK-Pfad (`_request_embedding_sdk`) mit HTTP-Fallback (`_request_embedding_http`) — **das ist kein "Silent Fallback auf lokal"**, sondern SDK→HTTP-Transport-Wahl für denselben Provider, bleibt unangetastet.
- `provider_from_profile()` (Z. 327-347) — Factory (siehe Punkt 2).
- `embedding_index_provider()` (Z. 54-65) — Identity-String `provider:model:dimensions`.
- `deterministic_embedding()` (Z. 67-82) — Hashbasierte Projektion hinter `LocalEmbeddingProvider`.

**KRITISCHER BEFUND — bestehender Anti-Pattern (genau das, was Prompt 26 verbietet):**
`OllamaEmbeddingProvider.embed()` (Z. 134-140) und `OpenAIEmbeddingProvider.embed()` (Z. 273-279):
```python
def embed(self, text: str) -> list[float]:
    try:
        return self._request_embedding(text)
    except Exception as exc:
        if self._fallback_allowed():
            return LocalEmbeddingProvider(self.dimensions).embed(text)  # <-- stiller Fallback
        raise RuntimeError("ollama_embedding_unavailable") from exc
```
Bei gesetztem `SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK=true` liefert `embed()` **kommentarlos einen deterministischen Fake-Vektor statt eines Fehlers**. `status()` markiert das zwar als `fallback_used: True`, aber der Aufrufer von `embed()` selbst bekommt keine Information — Ingest/Reindex/Search laufen "erfolgreich" durch. Das ist die Wurzel des in Prompt 26 verlangten Verbots.

### 2. Provider Factory

`secondbrain/p1_embeddings.py::provider_from_profile()` (Z. 327-347) — dispatcht über `cfg.provider` (`"ollama"|"openai"`, sonst **fällt implizit auf `LocalEmbeddingProvider` zurück**, Z. 347 — kein expliziter Allow-Gate hier, im Gegensatz zu Stack A/C). Das ist separat vom Laufzeit-Fallback in `embed()` und für sich harmlos (wird nur bei `provider == "local"/"local-deterministic"/"deterministic"` erreicht, was `evaluate_embedding_config` in Produktion ohnehin blockt), aber die fehlende Explizitheit wird in Phase 1 durch eine explizite Prüfung ersetzt.

### 3. RAG-Konfiguration

`secondbrain/p1_embedding_config.py`:
- `EmbeddingConfig` (Z. 47-70, `frozen=True`) — Felder: `provider, model, dimensions, ollama_base_url, openai_api_key_env, allow_fallback, timeout_seconds, source, dimensions_source`.
- `load_embedding_config()` (Z. 86-126) — Precedence: Env-Vars → `config/vector_rag.yaml` → Defaults. `KNOWN_PROVIDERS` (Z. 10), `PRODUCTION_PROVIDERS = {"ollama", "openai"}` (Z. 11).
- `evaluate_embedding_config()` (Z. 129-172) — Production-Gate auf Config-Ebene: blockt bereits nicht-Produktionsprovider, `allow_fallback` in Produktion, fehlenden OpenAI-Key, ungültige Ollama-URL, zu kleine Dimensionen, ungültigen Timeout. **Das ist bereits eine solide Basis für "misconfigured".**

### 4. Provider Health

`secondbrain/p1_provider_health.py::evaluate_embedding_provider_health()` (Z. 17-68) — kombiniert `provider.status()` mit `evaluate_embedding_config()`, produziert `blockers`/`warnings` (u.a. `local_deterministic_embeddings_not_allowed_for_production`, `embedding_dimension_contract_failed`, `embedding_fallback_cannot_prove_production_readiness`). Schreibt `runtime/reports/p1_provider_health_latest.json`.

### 5. Production Gate

`secondbrain/p1_production_gate.py::production_gate_with_golden()` (Z. 27-114) — der **scharfgeschaltete** Gate, aufgerufen von `launcher.py p1-production`. Komponiert: `runtime.production_gate()` (Basis), `evaluate_golden_retrieval` (Retrieval-Qualität, aus Prompt 27), `evaluate_embedding_provider_health` (Punkt 4), `audit_vector_provider` (Punkt 6). Schreibt `runtime/reports/p1_production_latest.json`.

### 6. Reindex-Mechanik

`secondbrain/p1_vector_provider_guard.py`:
- `audit_vector_provider()` (Z. 199-213) — vergleicht `embedding_index_provider(runtime.embedding_provider)` (aktuelle Identity) gegen gespeicherte Vektoren (`rag_store.validation_snapshot()` oder SQLite-Legacy), erkennt `stale_vector_provider`, `dimension_mismatch_vectors`, `missing_vectors`, `orphan_vectors`.
- `repair_vector_index()` (Z. 216-276) — repariert die reparierbare Teilmenge via `runtime.reindex_vectors()`, blockt bei strukturellen Fehlern (`orphan_vectors`).
- **Läuft aktuell nur als Batch-Audit (Gate-Check), nicht als Live-Block beim Suchaufruf.** `P1RagRuntime.vector_search()` (`p1_rag_runtime.py` Z. 376-428) prüft vor dem eigentlichen Query nur `_embedding_provider_blocker()` (Z. 181-195) — das blockt bei unhealthy Provider **außer** `fallback_allowed=True` ist gesetzt (Z. 185: `not fallback_allowed`). Nach Entfernen des stillen Fallbacks in Phase 1 wird dieser Pfad automatisch hart (da `embed()` dann wirft und `_embedding_failure_payload` greift) — **`p1_rag_runtime.py` muss dafür nicht geändert werden**, das ist bewusst außerhalb des Datei-Budgets gehalten.

### 7. Bestehende Tests — Namenskonflikt und Breaking-Change-Risiko

Die drei im Auftrag genannten Dateien existieren **nicht**:
- `tests/test_embedding_providers.py` — nicht vorhanden → neu anzulegen.
- `tests/test_embedding_provider_health.py` — nicht vorhanden → neu anzulegen.
- `tests/test_p1_production_gate.py` — nicht vorhanden → neu anzulegen.

Funktional äquivalente/überlappende Bestandstests (bleiben als Regressionsschutz bestehen, dürfen nicht kaputtgehen — mit einer Ausnahme, siehe unten):
- `tests/test_v186_p1_production_golden_gate.py` — End-to-End-Muster für `production_gate_with_golden()` direkt über `P1RagRuntime(tmp_path)`, ohne Mocks (Referenzmuster für Phase 3).
- `tests/test_v3012_p1_provider_health_gate.py` — Referenzmuster für `evaluate_embedding_provider_health()` + Launcher-Assertion + `ModuleRegistry`-Check.
- `tests/test_v187_p1_vector_provider_guard.py`, `test_v3014..3017_*` — Config-/Dimension-/Identity-Contract-Tests, unverändert lassen.
- `tests/test_v3016_p1_embedding_http_provider.py` (Z. 38, 58) — zeigt das Injection-Muster `monkeypatch.setattr(p1_embeddings.request, "urlopen", fake_urlopen)` für simulierte HTTP-Antworten (Referenzmuster für Phase 3, `misconfigured`/`incompatible`-Tests).
- `tests/test_v184_p1_embeddings_vectorstore.py` (Z. 155, 169, 184) — zeigt das Muster "geschlossener Port" `OllamaEmbeddingProvider(base_url="http://127.0.0.1:9", timeout_seconds=0.01)` für schnelle, echte `unavailable`-Tests ohne Mock (Referenzmuster für Phase 3).

**Breaking Change (bewusst, muss im Plan stehen):** `tests/test_v184_p1_embeddings_vectorstore.py` enthält zwei Tests, die den zu entfernenden Anti-Pattern als korrektes Verhalten voraussetzen:
- `test_openai_embedding_provider_...fallback...` (ca. Z. 137-150): `provider.embed("fallback path")` erwartet einen 16-dim Vektor via Fallback, `status["fallback_used"] is True`.
- `test_ollama_embedding_provider_fallback_requires_explicit_opt_in` (Z. 167-179): identisches Muster für Ollama.

Diese zwei Tests müssen in Phase 1/3 umgeschrieben werden (assert `pytest.raises(RuntimeError, match="...")` statt assert-Fallback-Vektor), da sie sonst nach der Härtung **korrekt fehlschlagen würden** — kein Wegwerfen, sondern Anpassung an die neue, geforderte Vertragslage. Das macht `tests/test_v184_p1_embeddings_vectorstore.py` zu einer vierten Testdatei im Scope.

### 8. launcher.py

1075 Zeilen, `main()` (Z. 823) dispatcht linear über `cmd in {...}`. Relevante Commands: `p1-provider-health`, `p1-embedding-config`, `p1-production`, `p1-vector-provider-audit`, `p1-vector-index-repair` — alle über den gemeinsamen `P1RagRuntime`-Dispatch-Block (Z. 881-953). **Keine Launcher-Änderung in diesem Plan nötig** — bestehende Commands geben nach der Härtung automatisch die neuen Felder/Blocker aus, da sie nur die Rückgabe-Payloads der geänderten Funktionen als JSON drucken.

### 9. Wiederverwendbare Bausteine (DRY — nicht neu erfinden)

- **Retry/Backoff:** `secondbrain/storage/db_retry.py::run_with_retry(fn, policy, transient=..., sleeper=...)` (Z. 37-55) + `RetryPolicy(max_attempts, base_delay, max_delay, multiplier)` (Z. 27-34) — generischer, bereits getesteter Retry-Helfer. Wird in Phase 1 mit einem embedding-spezifischen `transient()`-Prädikat wiederverwendet statt neu gebaut.
- **Secret-Redaction:** `secondbrain/safe_logging.py::redact()` — vorhanden, aber **nicht nötig**: `status()`/Fehlermeldungen in `p1_embeddings.py` enthalten bereits heute keine API-Key-Werte (nur `api_key_configured: bool`) und keine Eingabetexte. Diese Invarianz wird in Phase 1 explizit erhalten (Guard), nicht neu gebaut.

---

## Architekturentscheidung: Provider-Modi als Klassifikationsfunktion

Die 5 geforderten Modi (`development`, `production`, `unavailable`, `misconfigured`, `incompatible`) existieren nirgends im Repo als Vokabular (verifiziert, Phase 0). Sie werden als reine Ableitung aus vorhandenen `status()`-Feldern berechnet — **keine neue Statushaltung, kein neuer State**:

```
development   := provider.name in {local, local-deterministic, deterministic}
misconfigured := config-level blocker (evaluate_embedding_config) ODER
                 error-code in {*_api_key_missing, unknown_embedding_provider,
                 *_http_error:401, *_http_error:403, ollama_base_url_invalid}
unavailable    := network-/timeout-Fehler (URLError, TimeoutError,
                 *_network_error, *_http_error:5xx, *_http_error:429)
incompatible   := dimension_contract_ok is False (Ist-Dimension != konfigurierte Dimension)
production     := ok is True und semantic is True und production_ready is True
                 und name not in DEV_ONLY_NAMES
```
Reihenfolge der Prüfung: `misconfigured` > `incompatible` > `unavailable` > `development` > `production` (Konfigurationsfehler haben Vorrang, da sie die Ursache für nachgelagerte Netzwerk-/Dimensionsfehler sein können).

---

## Phase 1 — Provider-Kern härten (2 Dateien)

**Dateien:** `secondbrain/p1_embeddings.py`, `secondbrain/p1_embedding_config.py`

### secondbrain/p1_embeddings.py

1. **Stillen Fallback entfernen** (Kernfix, Commit-Zweck): In `OllamaEmbeddingProvider.embed()` (Z. 134-140) und `OpenAIEmbeddingProvider.embed()` (Z. 273-279) die `if self._fallback_allowed(): return LocalEmbeddingProvider(...).embed(text)`-Zweige löschen. `embed()` wirft in jedem Fehlerfall `RuntimeError`, unabhängig von `allow_fallback`/Env-Var. Die Felder `allow_fallback`/`fallback`/`_fallback_allowed()` bleiben als reine **Beobachtungsgrößen** in `status()` erhalten (Warnung, kein Verhaltensschalter mehr) — nicht löschen, nur entkoppeln.
2. **Fehlerklassifikation einführen:** neue Funktion `classify_provider_mode(status: dict) -> str` nach obiger Architekturentscheidung. Exportiert für Wiederverwendung in Phase 2.
3. **DEV_ONLY explizit machen:** Konstante `DEV_ONLY_PROVIDER_NAMES = {"local-deterministic", "local", "deterministic"}` (mit `p1_embedding_config.KNOWN_PROVIDERS - PRODUCTION_PROVIDERS` abgleichen, keine Divergenz).
4. **Retry mit Backoff** um `_request_embedding()`-Aufrufe in `embed()` (nicht in `status()`-Health-Probe — die bleibt Single-Shot, damit Health-Checks nicht künstlich verzögert werden): `run_with_retry` aus `secondbrain.storage.db_retry` importieren, `RetryPolicy(max_attempts=cfg.max_retries, base_delay=cfg.retry_base_delay_seconds)`. `transient()`-Prädikat: `True` nur für `urllib.error.URLError`, `TimeoutError`/`socket.timeout`, sowie `RuntimeError`-Messages mit Präfix `*_network_error` oder `*_http_error:5` /`*_http_error:429`. **Kein Retry** bei `*_api_key_missing`, `*_embedding_dimension_mismatch`, `*_http_error:401`, `*_http_error:403`, `unknown_embedding_provider` (exakt die Regel "kein Retry bei Auth-/Konfigurationsfehlern").
5. **Latenzmessung:** in `status()` per `time.perf_counter()` um den Health-Probe-Call, neues Feld `latency_ms: float`.
6. **Batchfähigkeit ehrlich berichten:** neues Feld `batch_capable: bool` in `status()`. `OpenAIEmbeddingProvider`: `True` (native Batch via `input: list[str]` in der HTTP/SDK-Payload) — `embed_batch(texts: list[str]) -> list[list[float]]` neu implementieren (echter Batch-Request, ein HTTP-Call). `OllamaEmbeddingProvider`: `False` (die genutzte `/api/embeddings`-Route nimmt nur ein `prompt`-Feld; `embed_batch()` als sequentielle Schleife implementieren, aber die Capability ehrlich als `False` melden — keine erfundene Batch-API annehmen). `LocalEmbeddingProvider`: `True` (kein Netzwerk, trivialer Loop).
7. **Reindex-Flag-Unterstützung:** `status()` bekommt Feld `reindex_required: bool` — `True`, wenn `embedding_index_provider(self)` von der zuletzt bekannten gespeicherten Identity abweicht. Dazu **kein neuer Speichermechanismus** — Provider bleibt zustandslos; das tatsächliche Vergleichen gegen den Store bleibt Aufgabe von `p1_vector_provider_guard.py` (Phase 2). Hier nur das Datenfeld vorbereiten (Default `None`/nicht gesetzt, wird von Phase 2 aus befüllt) — **Alternative, einfachere Lösung:** Feld ganz weglassen aus `status()` und `reindex_required` ausschließlich in `audit_vector_provider()` (Phase 2) berechnen, wo der Store-Vergleich ohnehin stattfindet. → Diese Alternative wird gewählt (KISS, keine Verantwortung duplizieren). Punkt 7 entfällt damit aus dieser Datei.
8. **Audit-Guard (keine Secrets/Texte):** Kommentar/Assertion-freundliche Sicherstellung, dass keine neue Codezeile `text`/`query`/API-Key-Werte in `RuntimeError`-Messages oder `status()` einbettet. Bestehende Invarianz nicht brechen.

### secondbrain/p1_embedding_config.py

1. **Neue Config-Felder** in `EmbeddingConfig` (Z. 47-57): `max_retries: int = 2`, `retry_base_delay_seconds: float = 0.2`. Env-Vars `SECONDBRAIN_EMBEDDING_MAX_RETRIES`, `SECONDBRAIN_EMBEDDING_RETRY_BASE_DELAY_SECONDS`, über die vorhandenen `_env_int`/`_env_float`-Helfer (Z. 21-44) — analog zu `timeout_seconds` (Z. 114). `to_dict()` (Z. 59-70) um beide Felder ergänzen.
2. **`DEV_ONLY_PROVIDERS`-Konstante** exportieren (`= KNOWN_PROVIDERS - PRODUCTION_PROVIDERS`), damit `p1_embeddings.py` sie referenziert statt eine zweite Quelle der Wahrheit zu pflegen.
3. `evaluate_embedding_config()` (Z. 129-172): keine Verhaltensänderung nötig — die Misconfigured-Blocker sind bereits vollständig (fehlender Key, ungültige URL, unbekannter Provider, ungültige Dimensionen/Timeout). Nur `mode: "misconfigured" if blockers else "ok"`-Feld in den Payload (Z. 156-165) ergänzen, additiv.

### Anti-Pattern-Guards (Phase 1)
- **Nicht tun:** keine vierte Provider-Klasse erfinden, keine neue Config-Datei, keine Änderung an `config/vector_rag.yaml`-Schema (bleibt kompatibel).
- **Nicht tun:** `allow_fallback`-Feld/Env-Var nicht komplett entfernen (Breaking Change für `status()`-Konsumenten) — nur seine Wirkung auf `embed()` kappen.
- **Nicht tun:** keine Ollama-Batch-API erfinden, die es nicht nachweislich gibt.

### Verifikation Phase 1
- `python -c "from secondbrain.p1_embeddings import OllamaEmbeddingProvider, OpenAIEmbeddingProvider, classify_provider_mode"` läuft ohne Fehler.
- Manuelle Probe: `OllamaEmbeddingProvider(base_url="http://127.0.0.1:9", timeout_seconds=0.01).embed("x")` wirft `RuntimeError`, **auch** mit `SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK=true` gesetzt.
- `git grep -n "fallback_allowed()" secondbrain/p1_embeddings.py` zeigt die Aufrufe nur noch in `status()`, nicht mehr in `embed()`.

---

## Phase 2 — Health, Gate, Reindex-Wiring (3 Dateien)

**Dateien:** `secondbrain/p1_provider_health.py`, `secondbrain/p1_production_gate.py`, `secondbrain/p1_vector_provider_guard.py`

### secondbrain/p1_provider_health.py

1. `evaluate_embedding_provider_health()` (Z. 17-68): `mode = classify_provider_mode(status)` aus Phase 1 importieren, in Payload (Z. 49-61) additiv als `"mode": mode` aufnehmen.
2. **8-Punkte-Health-Check explizit als Teil-Checks abbilden** (statt nur Blocker-Strings): neues Feld `checks: dict[str, bool|float|None]` mit genau den geforderten Dimensionen:
   - `reachable`: `bool(status.get("ok"))`
   - `model_present`: `status.get("model") is not None` (bzw. spezifischer, falls Provider-Antwort ein Modell-Feld bestätigt)
   - `dimension_correct`: `status.get("dimension_contract_ok")`
   - `test_embedding_ok`: `bool(status.get("ok"))` (die Health-Probe in `status()` IST der Test-Embedding-Aufruf)
   - `latency_ms`: `status.get("latency_ms")` (aus Phase 1)
   - `batch_capable`: `status.get("batch_capable")` (aus Phase 1)
   - `production_ready`: `bool(status.get("production_ready"))`
   - `reindex_required`: aus `audit_vector_provider()` (siehe unten) — **nur befüllbar, wenn ein `runtime.rag_store` existiert**; sonst `None` mit Begründung, kein Blocker.
3. **Bestehende Blocker-Strings NICHT umbenennen** (Regressionsschutz für `test_v3012_p1_provider_health_gate.py` Z. 19: `"local_deterministic_embeddings_not_allowed_for_production"`) — nur ergänzen, z. B. zusätzlich `"dev_only_provider_blocked_in_production"` als Alias-Blocker parallel setzen, falls der Auftrag exakt diesen Begriff in Akzeptanztests erwartet (Abgleich in Phase 3 anhand der tatsächlichen Testerwartung, nicht vorab hart kodieren).

### secondbrain/p1_production_gate.py

1. `production_gate_with_golden()` (Z. 27-114): DEV_ONLY-Block bereits über `provider_health`-Check (Z. 60-76) abgedeckt — additiv `"mode"` und `"checks"` (aus Phase 2.1/2.2) in das `detail`-Dict (Z. 65-74) übernehmen, damit der Production-Gate-Report die 5-Modi-Klassifikation sichtbar macht.
2. Keine neue Blocker-Logik nötig — Gate aggregiert nur, Blocker-Erzeugung bleibt in `p1_provider_health.py`/`evaluate_embedding_config`.

### secondbrain/p1_vector_provider_guard.py

1. `audit_vector_provider()` / `_audit_from_snapshot()` (Z. 34-120) und `_audit_sqlite_legacy()` (Z. 123-196): neues Top-Level-Feld `reindex_required: bool` = `bool(stale_vectors or dimension_mismatch_vectors or missing_vectors)` — reine Umbenennung/Alias der bereits vorhandenen Blocker-Kombination in ein explizites Flag (Prompt-Wortlaut "Reindex-Flag setzen").
2. **Providerwechsel-Tracking:** neues Feld `previous_provider`/`provider_changed: bool` in der Audit-Payload — Vergleich `current_provider` (Z. 40/126) gegen den in `provider_inventory`/`providers` (Z. 82-85/170) am häufigsten vertretenen Alt-Eintrag (sofern vorhanden). Kein neuer Persistenzmechanismus — die Information steckt bereits in den gespeicherten `chunk_embeddings`-Zeilen (`provider`-Spalte), nur bisher nicht als "vorheriger Provider" benannt.
3. **Suche blockieren bei Inkompatibilität:** `audit_vector_provider()` liefert bereits `status: "blocked"` bei `dimension_mismatch_vectors`/`stale_vector_provider`. Das reicht als **Gate-Level-Block** (Production Gate, Akzeptanztest 9). Ein **Live-Block direkt im Suchpfad** (`P1RagRuntime.vector_search`) ist laut Phase-0-Analyse (Punkt 6) bereits indirekt gegeben, sobald Phase 1 den stillen Fallback entfernt — kein Zugriff auf `p1_rag_runtime.py` nötig, Datei bleibt außerhalb des Budgets.

### Anti-Pattern-Guards (Phase 2)
- **Nicht tun:** keine bestehenden `blockers`-Stringwerte umbenennen oder entfernen (bricht `test_v3012`, `test_v186`, `test_v3013..3017`).
- **Nicht tun:** kein neues Report-Schema-Präfix einführen (`p1_provider_health.v2` bleibt v2, additive Felder rechtfertigen keinen Versionssprung).
- **Nicht tun:** `p1_rag_runtime.py` nicht anfassen (Datei-Budget, siehe Phase-0-Begründung).

### Verifikation Phase 2
- `pytest -q tests/test_v3012_p1_provider_health_gate.py tests/test_v186_p1_production_golden_gate.py tests/test_v187_p1_vector_provider_guard.py` — müssen weiterhin grün sein (Regressionsschutz).
- Report-Dateien (`runtime/reports/p1_provider_health_latest.json`, `p1_production_latest.json`) enthalten manuell geprüft die neuen Felder (`mode`, `checks`, `reindex_required`) ohne API-Keys/Eingabetexte.

---

## Phase 3 — Tests (4 Dateien)

**Dateien:** `tests/test_embedding_providers.py` (neu), `tests/test_embedding_provider_health.py` (neu), `tests/test_p1_production_gate.py` (neu), `tests/test_v184_p1_embeddings_vectorstore.py` (Anpassung, 2 Tests)

Referenzmuster (aus Phase 0 verifiziert, wörtlich übernehmen):
- Geschlossener Port für `unavailable` ohne Mock: `OllamaEmbeddingProvider(base_url="http://127.0.0.1:9", timeout_seconds=0.01, dimensions=16)` (`test_v184` Z. 155).
- `monkeypatch.setattr(p1_embeddings.request, "urlopen", fake_urlopen)` für kontrollierte HTTP-Antworten/-Fehler (`test_v3016` Z. 38, 58) — für `misconfigured` (401) und `incompatible` (falsche Dimension in der Antwort).
- End-to-End über echtes `P1RagRuntime(tmp_path)` ohne Fakes, plus `launcher.main([...])`-Assertion (`test_v186`, `test_v3012`).

### tests/test_embedding_providers.py (neu)
- Lokaler Provider läuft in Development: `LocalEmbeddingProvider().status()["production_ready"] is False`, `classify_provider_mode(...) == "development"`. *(Akzeptanztest 1)*
- Kein stiller Fallback: `OllamaEmbeddingProvider(base_url="http://127.0.0.1:9", ...)` und `OpenAIEmbeddingProvider(...)` werfen `RuntimeError` bei `embed()`, **auch mit** `monkeypatch.setenv("SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK", "true")`. *(Akzeptanztest 5)*
- OpenAI offline → `unavailable`: `monkeypatch.setattr(..., "urlopen", raises URLError)` → `classify_provider_mode(status) == "unavailable"`. *(Akzeptanztest 3)*
- Ollama offline → `unavailable`: geschlossener Port, analog. *(Akzeptanztest 4)*
- Dimensionsabweichung → `incompatible`: `fake_urlopen` liefert Vektor falscher Länge, `enforce_dimensions=True` → `dimension_contract_ok is False`, `classify_provider_mode(...) == "incompatible"`. *(Akzeptanztest 6)*
- Fehlende Konfiguration → `misconfigured`: `OpenAIEmbeddingProvider` ohne `OPENAI_API_KEY` env → Fehlercode `openai_api_key_missing` → `classify_provider_mode(...) == "misconfigured"`. *(Regel aus Auftrag Punkt 3)*
- Retry-Verhalten: `fake_urlopen`, das erst 2x `URLError` wirft, dann Erfolg → `embed()` liefert Vektor, Aufrufzähler == 3 (Retries griffen). Zweiter Test: `fake_urlopen` wirft `HTTPError(401)` → **kein** zweiter Aufruf (kein Retry bei Auth-Fehler).
- API-Keys nicht in Status/Fehlern: `assert os.environ["OPENAI_API_KEY"] not in json.dumps(status)` nach echtem/simuliertem Health-Call. *(Akzeptanztest 8, teilweise — Rest in test_embedding_provider_health.py)*

### tests/test_embedding_provider_health.py (neu)
- 8-Punkte-Health-Check vollständig: `evaluate_embedding_provider_health(rt, production=True)["provider_status"]["checks"]` enthält alle 8 Schlüssel (`reachable, model_present, dimension_correct, test_embedding_ok, latency_ms, batch_capable, production_ready, reindex_required`).
- Lokaler Provider blockiert Production: `P1RagRuntime(tmp_path)` (Default = local) → `evaluate_embedding_provider_health(rt, production=True)["ok"] is False`, Blocker enthält weiterhin `"local_deterministic_embeddings_not_allowed_for_production"` (Regressionsschutz, wörtlich wie `test_v3012` Z. 19). *(Akzeptanztest 2)*
- Providerwechsel setzt Reindex-Flag: `P1RagRuntime` mit Provider A ingest, dann `rt.embedding_provider = <Provider B>`, `audit_vector_provider(rt)["reindex_required"] is True`. *(Akzeptanztest 7)*
- Keine API-Keys im Report: `runtime/reports/p1_provider_health_latest.json` nach `write_report=True` einlesen, `assert api_key_value not in report_text`.

### tests/test_p1_production_gate.py (neu)
- Production Gate blockiert bei nicht-produktivem Provider: `production_gate_with_golden(P1RagRuntime(tmp_path), tmp_path)["ok"] is False` (Default-Provider ist local). *(Akzeptanztest 9, deckungsgleich mit `test_v3012` Z. 39-47 — hier als eigenständiger, benannter Test dupliziert, da Auftrag exakt diese Datei verlangt.)*
- `launcher.main(["--project-root", str(tmp_path), "p1-production", "--write-report"])` liefert `rc == 1` bei lokalem Dev-Provider, `rc == 0`-Pfad wird **nicht** gegen echtes Netzwerk getestet (kein Live-Call in CI) — stattdessen Assertion, dass bei injiziertem, gesund simuliertem Provider (`monkeypatch` auf `_request_embedding`) der Gate-Check `embedding_provider_production_ready` `ok: True` liefert.
- Report enthält `mode`-Feld je Provider-Check.

### tests/test_v184_p1_embeddings_vectorstore.py (Anpassung)
- `test_openai_embedding_provider_...fallback...` (ca. Z. 128-150) umschreiben: `SECONDBRAIN_EMBEDDING_ALLOW_FALLBACK=true` gesetzt lassen (Doku-Zweck: Flag hat keine Wirkung mehr auf `embed()`), aber `pytest.raises(RuntimeError, match="boom")` statt Fallback-Vektor-Assertion. `status()["fallback_used"]` darf weiterhin `True` melden (reine Beobachtungsgröße), aber `embed()` wirft.
- `test_ollama_embedding_provider_fallback_requires_explicit_opt_in` (Z. 167-179) analog umbenennen (z. B. `test_ollama_embedding_provider_never_falls_back_even_with_opt_in`) und auf `pytest.raises` umstellen.
- Alle übrigen Tests in dieser Datei unverändert lassen.

### Anti-Pattern-Guards (Phase 3)
- **Nicht tun:** keine echten Netzwerkaufrufe gegen `api.openai.com` in der Standard-Testsuite (nur in `test_live_gated.py`, unangetastet, ohnehin `pytest.skip` ohne echten Key).
- **Nicht tun:** keine Sleep-Zeiten > 1s in Retry-Tests — `RetryPolicy(base_delay=0.01, max_delay=0.05)` injizieren, `sleeper` in Tests durch No-Op ersetzen (Muster aus `db_retry.run_with_retry(..., sleeper=...)`).

### Verifikation Phase 3
```
pytest -q tests/test_embedding_providers.py
pytest -q tests/test_embedding_provider_health.py
pytest -q tests/test_p1_production_gate.py
pytest -q tests/test_v184_p1_embeddings_vectorstore.py
```
Alle vier grün, keine Warnings zu unclosed sockets/Timeouts > 1s Gesamtlaufzeit pro Datei.

---

## Phase 4 — Verifikation & Abschluss (keine neuen Dateien)

1. Branch erstellen: `git checkout -b feature/v30.87-embedding-production`.
2. Vollständige Zielsuite:
   ```
   pytest -q tests/test_embedding_providers.py
   pytest -q tests/test_embedding_provider_health.py
   pytest -q tests/test_p1_production_gate.py
   ```
3. Regressionsschutz — angrenzende Bestandstests:
   ```
   pytest -q tests/test_v184_p1_embeddings_vectorstore.py tests/test_v186_p1_production_golden_gate.py tests/test_v187_p1_vector_provider_guard.py tests/test_v3012_p1_provider_health_gate.py tests/test_v3013_p1_golden_quality_gate.py tests/test_v3014_p1_embedding_config_contract.py tests/test_v3015_p1_embedding_dimension_contract.py tests/test_v3016_p1_embedding_http_provider.py tests/test_v3017_p1_embedding_index_identity.py
   ```
4. Volle Suite (Release-Gate-Anforderung aus CLAUDE.md — "keine Regressionen"): `pytest -q`.
5. Schritt-0-Check (CLAUDE.md): `git grep -n "fallback_allowed()" secondbrain/p1_embeddings.py` → nur in `status()`, kein toter Code, keine ungenutzten Imports (`ruff`/vorhandener Linter, falls konfiguriert — prüfen mit `python -m pyflakes secondbrain/p1_embeddings.py secondbrain/p1_embedding_config.py secondbrain/p1_provider_health.py secondbrain/p1_production_gate.py secondbrain/p1_vector_provider_guard.py`).
6. Akzeptanztest-Checkliste (1-9 aus Auftrag) explizit gegen die in Phase 3 geschriebenen Tests abgleichen — 1:1-Zuordnung dokumentieren.
7. Commit:
   ```
   git add secondbrain/p1_embeddings.py secondbrain/p1_embedding_config.py secondbrain/p1_provider_health.py secondbrain/p1_production_gate.py secondbrain/p1_vector_provider_guard.py tests/test_embedding_providers.py tests/test_embedding_provider_health.py tests/test_p1_production_gate.py tests/test_v184_p1_embeddings_vectorstore.py
   git commit -m "fix(embeddings): enforce production provider readiness"
   ```
8. **Nicht pushen** ohne explizite Freigabe.

---

## Offene Entscheidungen / Annahmen, die im Ausführungs-Kontext zu bestätigen sind

1. **"Ändere maximal fünf Dateien"** wird als **Pro-Phase-Limit** interpretiert (konsistent mit CLAUDE.md "Arbeit in Phasen von maximal fünf Dateien aufteilen"), nicht als harte Gesamtgrenze — bei 3 fragmentierten Stacks und 3 pflichtigen, neu zu erstellenden Testdateinamen ist eine Gesamtgrenze von 5 Dateien nicht einhaltbar, ohne Funktionsumfang zu unterschlagen. Gesamt: 9 Dateien über 3 Phasen (2+3+4).
2. **Breaking Change an `tests/test_v184_p1_embeddings_vectorstore.py`** ist beabsichtigt und notwendig (siehe Phase 0, Punkt 7) — falls unerwünscht, müsste der Auftrag selbst geändert werden (Fallback-Verbot zurücknehmen), was dem expliziten Auftragstext widerspräche.
3. Der exakte Blocker-String `"dev_only_provider_blocked_in_production"` wird nur ergänzt, falls Akzeptanztest-Formulierungen ihn wörtlich verlangen — sonst bleibt der bestehende String `"local_deterministic_embeddings_not_allowed_for_production"} maßgeblich, um keine Doppel-Blocker-Inflation zu erzeugen.
