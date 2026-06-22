# SecondBrain-Agent v17.9 P0 – Production Gate & Artifact Audit

## Ziel

v17.9 schließt die P0-Härtung für wiederholbare lokale Betriebsfähigkeit. Der Stand prüft nicht nur Launcher, Registry, Readiness und Smoke, sondern erzeugt eine vollständige P0-Evidenzkette für CI, Support und Release-Entscheidung.

## Neue Commands

```bash
python launcher.py p0-production --write-report
python launcher.py p0-audit --write-report
```

## p0-production

Führt die vollständige P0-Sequenz aus:

1. `p0-bootstrap`
2. `p0-contract`
3. `p0-readiness`
4. `p0-gate`
5. `p0-smoke`
6. `p0-audit`

Ergebnisdatei:

```text
runtime/reports/p0_production_gate_latest.json
```

## p0-audit

Prüft lokale Betriebsartefakte:

- `launcher.py`
- `secondbrain/p0_runtime.py`
- P0-Integrationstests
- Report-Verzeichnis
- Gate-/Readiness-/Smoke-/Contract-Reports
- Runtime-Recovery-State
- Event-Log
- JSON-Validität der Reports

Ergebnisdatei:

```text
runtime/reports/p0_artifact_audit_latest.json
```

## Gate-Logik

Blockierend:

- Launcher fehlt
- P0-Runtime fehlt
- P0-Tests fehlen
- Runtime-State fehlt
- Event-Log fehlt oder leer
- JSON-Report ungültig
- Bootstrap/Contract/Readiness/Gate/Smoke/Audit schlägt fehl

Nicht blockierend:

- Keine produktive PostgreSQL-URL
- Keine pgvector-Deklaration
- Entwicklungsmodus für Secrets

Diese Punkte bleiben P1/P2-Produktionshärtung, blockieren aber P0 nicht.

## Validierung v17.9

```text
python launcher.py p0-production --write-report: PASS
python launcher.py p0-audit --write-report: PASS
pytest -q: 249 passed
```

## Ergebnis

P0 ist jetzt lokal wiederholbar prüfbar. Nächster sinnvoller Block ist P1: echte Config-/Secret-Verwaltung, PostgreSQL/pgvector, Repository Layer und Connector-Integration.
