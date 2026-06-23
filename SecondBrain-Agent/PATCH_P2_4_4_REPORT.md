# PATCH P2.4.4 — Saved Searches

## Inhalt

- `secondbrain/desktop/search/saved_searches.py`
  - `SavedSearch`
  - `SavedSearchRepository`
  - `SavedSearchService`
  - `SavedSearchError`
- `tests/desktop/search/test_saved_searches.py`
- `pytest.ini`

## Funktionen

- Gespeicherte Suchabfragen erstellen, lesen, aktualisieren, löschen
- JSON-Persistenz
- Query-Payload für Search-Service erzeugen
- Validierung von Name, Query, Limit und Listenfeldern
- Deduplizierung von Tags/Status/Sources
- Case-insensitive Duplicate-Name-Schutz

## Validierung

`6 passed in 0.22s`
