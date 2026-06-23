# PATCH P2.3.3 — Document Preview

## Inhalt
- `document_preview.py`
  - sicheres Preview-ViewModel
  - Statuswerte `READY`, `EMPTY`, `FAILED`, `UNSUPPORTED`, `ARCHIVED`
  - MIME-/Dateiendungs-Erkennung
  - Zeichen- und Zeilenbegrenzung
  - erlaubnisbasierte Preview-Metadaten
- `document_preview_service.py`
  - Repository-basierter Preview-Zugriff
  - klarer NotFound-Fehler
- Tests für Textvorschau, Trunkierung, Unsupported, Failed, Archived, Metadaten-Allowlist und Service-Fehlerpfad

## Validierung
- `8 passed`

## Risiko reduziert
- Keine unbounded GUI-Vorschau großer Inhalte
- Keine technischen IDs oder Secrets in Preview-Metadaten
- Binär-/Unsupported-Dateien erzeugen stabile Statusobjekte statt UI-Fehler
