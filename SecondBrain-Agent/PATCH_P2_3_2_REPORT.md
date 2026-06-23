# PATCH P2.3.2 — Document Detail View

## Inhalt
- `document_detail.py`
  - user-facing Detail-ViewModel
  - technische ID-Felder nicht sichtbar
  - Metadaten-Sanitizing für IDs, Secrets, Tokens
  - Gruppenfilter für Summary/Timeline
- `document_detail_service.py`
  - Repository-basierter Detailzugriff
  - klarer NotFound-Fehler
- Tests für Detailmodell, Sanitizing, Service und Fehlpfad

## Validierung
- `7 passed`

## Risiko reduziert
- Keine sichtbaren technischen IDs in der Dokument-Detailansicht
- Keine token-/secret-artigen Metadaten in GUI-Modellen
- Stabile Trennung zwischen interner Referenz und sichtbaren Feldern
