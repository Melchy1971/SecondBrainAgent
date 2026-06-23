# Patch P2.2.2 – Dashboard Widgets

## Inhalt

- Konkrete Provider für alle Standard-Dashboard-Widgets eingeführt
- Workspace-gebundene Datenabfrage über injizierbare Fetch-Funktionen
- Health-Farben `green/yellow/red/unknown`
- Deterministische Aggregation für Jobs, Connectoren, RAG, System, Storage und Errors
- Default-Provider-Factory für Dashboard-Service

## Neue Datei

- `secondbrain/desktop/dashboard/widget_providers.py`

## Validierung

```text
10 passed
```

## Nächster Schritt

P2.2.3 Dashboard Layout-System: Layout-Slots, Widget-Positionen, Größen, Reihenfolge und Persistenz.
