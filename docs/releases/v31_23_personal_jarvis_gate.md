# v31.23 Personal Jarvis Gate

## Ziel

Das Gate bündelt die vorhandenen Personal-Jarvis-Subsysteme in einem kontrollierten, nebenwirkungsfreien Releasecheck.

Geprüft werden:

- Aufgaben und Projekte
- Planner V2
- persistente Langläufer
- Daily Briefing
- Memory Consolidation
- Kalenderassistent
- Mail-Assistent
- Proaktive Assistenz
- Persönliches Dashboard
- Review-/Approval-Governance
- Knowledge Graph als derzeit nichtkritische Ausbaustufe

## Ausführung

```bash
python scripts/personal_jarvis_gate.py --project-root .
```

Ohne Reportdatei:

```bash
python scripts/personal_jarvis_gate.py --project-root . --no-write-report
```

Der maschinenlesbare Report wird standardmäßig unter folgendem Pfad geschrieben:

```text
runtime/reports/personal_jarvis_gate.json
```

## Bewertung

- `PASS`: Private-Beta-fähig
- `CONDITIONAL_PASS`: Private Beta mit nichtkritischen Warnungen
- `BLOCKED`: nicht freigeben

## Sicherheitsprinzipien

- Das Gate führt keine externen Schreibaktionen aus.
- Es sendet keine E-Mails und verändert keine Kalenderdaten.
- Es verarbeitet keine Dokumentinhalte.
- Zusätzliche Runtime-Probes müssen ihre Ergebnisse auf Status und Detail reduzieren.
- Probe-Payloads werden nicht in den Report übernommen.

## Aktueller Umfang

Der erste Stand prüft stabile öffentliche Modulverträge. Reale Provider-, Connector- und User-Journey-Tests können über `extra_probes` ergänzt werden, ohne das Reportschema zu verändern.

## Tests

```bash
pytest -q tests/test_personal_jarvis_gate.py
```

## Restrisiko

Der Knowledge Graph ist im ersten Gate-Stand als nichtkritische Warnung modelliert, solange das produktive Graph-RAG-Modul noch nicht vollständig verfügbar ist. Alle übrigen Kernmodule sind harte Releasebedingungen.
