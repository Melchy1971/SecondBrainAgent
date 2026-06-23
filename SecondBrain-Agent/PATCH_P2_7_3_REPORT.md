# PATCH P2.7.3 – Accessibility & Error States

## Inhalt
- Einheitliches UI-State-Modell für Loading, Empty, Warning, Error, Ready
- ErrorCatalog mit Recovery-Aktionen und Screenreader-Hints
- Empty-State-Factory für Dokumente, Suche und Connectoren
- FocusManager für Tastaturnavigation
- KeyboardMap mit Standard-Shortcuts
- AccessibilityAudit für blockierende Zustände und fehlende Hinweise

## Validierung
- pytest: 8 passed

## Risiko reduziert
- Unklare Fehlerzustände
- Nicht-actionable Empty States
- Fehlende Recovery-Hinweise
- Fehlende Accessibility-Metadaten
