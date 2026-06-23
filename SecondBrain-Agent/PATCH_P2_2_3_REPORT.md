# Patch P2.2.3 – Dashboard Layout-System

## Inhalt

- Grid-basiertes Layout-Modell eingeführt
- Widget-Positionen mit `x`, `y`, `width`, `height`
- Kollisionsprüfung über belegte Grid-Zellen
- Validierung für negative Positionen, ungültige Größen, Spaltenüberschreitung, Duplikate und unbekannte Widgets
- Persistenz über `.config/dashboard/layout.json`
- Service-Schicht für validiertes Platzieren und Entfernen von Widgets

## Neue Dateien

- `secondbrain/desktop/dashboard/layout.py`
- `tests/desktop/dashboard/test_dashboard_layout.py`

## Geänderte Dateien

- `secondbrain/desktop/dashboard/__init__.py`

## Validierung

```text
6 passed
```

## Nächster Schritt

P2.2.4 Dashboard Actions: Widget-Aktionen, Deep Links, Refresh einzelner Widgets, Navigation zu Detailansichten.
