# SecondBrain OS v10.4 Connector Runtime

## Zweck

v10.4 verbindet externe Quellen nicht direkt mit Agenten, sondern über eine kontrollierte Pipeline:

```text
Connector → Normalizer → Runtime Event Store → Memory/RAG/Agent Runtime
```

## Implementierte Bausteine

| Datei | Funktion |
|---|---|
| `secondbrain/runtime_events_v104.py` | kanonisches Event-Schema, JSONL Event Store |
| `secondbrain/normalizer_v104.py` | Normalisierung für E-Mail, Kalender, Dokumente |
| `secondbrain/connector_runtime_v104.py` | Connector Registry, LocalJsonConnector, Sync-Orchestrierung |
| `scripts/run_v104_connector_sync.py` | ausführbarer Sync-Lauf |
| `config/connectors_v104.json` | deklarative Connector-Konfiguration |

## Sicherheitsprinzipien

- Standardmodus: read-only.
- Keine Live-Zugangsdaten im Repository.
- Externe API-Connectoren werden erst nach Permission Engine produktiv aktiviert.
- Jedes importierte Objekt wird als Event abgelegt.
- Schreibaktionen sind nicht Bestandteil von v10.4.

## Ausführung

```bash
cd SecondBrainAgent/SecondBrain-Agent
python scripts/run_v104_connector_sync.py
```

## Ergebnis

Events werden unter `events/runtime/YYYY-MM-DD.jsonl` gespeichert.
