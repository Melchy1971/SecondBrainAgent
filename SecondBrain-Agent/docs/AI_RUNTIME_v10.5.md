# SecondBrain OS v10.5 AI Runtime Foundation

## Zweck

v10.5 entkoppelt Aufgaben von konkreten Modellanbietern.

```text
Task → Context Builder → Model Router → Provider → Validator → Antwort
```

## Implementierte Bausteine

| Datei | Funktion |
|---|---|
| `secondbrain/ai_runtime_v105.py` | ModelRouter, EchoProvider, OllamaProvider, Response Validation |
| `config/ai_runtime_v105.yaml` | Provider-Konfiguration |
| `scripts/run_v105_ai_runtime.py` | Demo-Lauf gegen Event Store |

## Provider

Aktiv:

- `echo`: deterministisch, offline, testbar

Vorbereitet:

- `ollama`: lokal über `ollama_client`

## Ausführung

```bash
cd SecondBrainAgent/SecondBrain-Agent
python scripts/run_v104_connector_sync.py
python scripts/run_v105_ai_runtime.py
```

## Produktionsregel

Cloud-Provider werden erst nach Secret Vault, Permission Engine und Audit Logging aktiviert.
