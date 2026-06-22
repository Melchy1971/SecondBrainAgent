# SecondBrain-Agent v17.8 P0 – Readiness & Bootstrap

## Ziel

v17.8 schließt die nächste P0-Integrationslücke: P0 prüft nicht mehr nur Launcher, Registry und Smoke-Status, sondern auch produktionsnahe Runtime-Abhängigkeiten.

## Neue Befehle

```bash
python launcher.py p0-readiness
python launcher.py p0-readiness --write-report
python launcher.py p0-bootstrap
python launcher.py p0-bootstrap --write-report
```

## Neue P0-Prüfbereiche

### 1. Config Readiness

Prüft Pflichtdateien:

- `config/settings.yaml`
- `config/runtime.yaml`
- `config/production.yaml`
- `config/security.yaml`
- `config/connectors.yaml`

### 2. Secrets Readiness

Prüft:

- `secrets.template.yaml` vorhanden
- keine Platzhalterwerte in live `secrets.yaml`
- Secret-Encryption-Modus deklariert

Bewertung:

- Platzhalter in live Secrets = Blocker
- fehlende Encryption-Deklaration = Warning

### 3. Database Readiness

Prüft:

- `DATABASE_URL` oder `production.database.url`, falls vorhanden
- PostgreSQL-URL als produktiver Zielstandard
- pgvector-Deklaration als Warning
- Fallback: lokale SQLite-Schreibprobe für P0 ohne externe Services

### 4. Event Bus Readiness

Prüft:

- Publish auf `event_bus_v121`
- Event-ID erzeugt
- Status gesund
- Komponente entspricht `event_bus_v121`

### 5. Runtime State Readiness

Prüft/erstellt:

- `runtime/`
- `runtime/reports/`
- `runtime/state/`
- `runtime/events_v121/`
- `runtime/state/runtime_recovery.json`

## Gate-Integration

`p0-gate` enthält jetzt zusätzlich:

- `p0_runtime_readiness`
- Readiness-Zusammenfassung
- Warning-Anzahl aus Secrets/Database Readiness

## Reports

Neue Reports:

- `runtime/reports/p0_readiness_latest.json`
- `runtime/reports/p0_bootstrap_latest.json`

Bestehende Reports bleiben erhalten:

- `runtime/reports/p0_gate_latest.json`
- `runtime/reports/p0_smoke_latest.json`
- `runtime/reports/p0_contract_latest.json`

## Validierung

```bash
PYTHONPATH=. pytest -q
# 246 passed
```

## Ergebnis

P0 ist robuster, weil die zentralen Laufzeitabhängigkeiten jetzt explizit prüfbar sind. Externe Services werden weiterhin nicht erzwungen; das ist bewusst, damit lokale Entwicklung und CI ohne PostgreSQL/OAuth/LLM starten können.
