# v31.31 – Provider Live Gate

## Ergebnis

`python launcher.py provider-live-gate` prüft konfigurierte OpenAI- und
Ollama-Provider mit synthetischen, öffentlichen Testinhalten. Nicht konfigurierte
optionale Provider bleiben `not_configured` und führen zu `CONDITIONAL_PASS`.
Pflichtprovider werden über `REQUIRED_LIVE_PROVIDERS` festgelegt.

In der aktuellen Entwicklungsumgebung waren OpenAI und Ollama bewusst nicht
konfiguriert. Der ausgeführte Gate-Lauf ergab deshalb `CONDITIONAL_PASS`; ein
echter Provider-Live-Nachweis liegt noch nicht vor.

## Prüfvertrag

Für jeden konfigurierten Provider erfasst der Report:

- Readiness, Modell, Fähigkeiten und Quelle (lokal oder Cloud)
- hartes Request-Timeout und Gesamtlatenz
- Chat-Antwort und strukturiertes JSON
- Embedding sowie erkannte Vektordimension
- Usage und konfigurierte Kostenschätzung
- redigierten Fehlercode und Retry-Einstufung

Das Gate lädt keine Ollama-Modelle herunter und wechselt Provider nicht still.
Jeder Probe ist explizit einem Provider zugeordnet. `PRIVACY_MODE=strict`
blockiert Cloud-Probes vor dem Netzwerkzugriff. Das Gate verwendet keine privaten
Dokumente, Prompts oder Nutzerdaten.

## Konfiguration

- `OPENAI_API_KEY` und `OPENAI_LIVE_MODEL`
- optional `OPENAI_EMBEDDING_MODEL`, `OPENAI_BASE_URL`
- `OLLAMA_LIVE_MODEL`
- optional `OLLAMA_EMBEDDING_MODEL`, `OLLAMA_BASE_URL`
- `REQUIRED_LIVE_PROVIDERS=openai,ollama`
- `PROVIDER_LIVE_TIMEOUT_SECONDS` (1 bis 120 Sekunden)
- `PROVIDER_LIVE_MAX_COST`
- optionale Preisparameter `OPENAI_INPUT_PER_1M` und `OPENAI_OUTPUT_PER_1M`

Secrets, Endpoints, Prompts und Antwortinhalte werden nicht in den Report
übernommen. Der Report liegt unter `runtime/reports/provider_live_gate.json`.

Status:

- `PASS`: alle konfigurierten Provider vollständig bereit
- `CONDITIONAL_PASS`: nur optionale Provider fehlen oder sind degradiert
- `BLOCKED`: Pflichtprovider fehlt, konfigurierter Provider ist nicht erreichbar,
  Privacy blockiert den Aufruf oder das Kostenlimit wurde überschritten
