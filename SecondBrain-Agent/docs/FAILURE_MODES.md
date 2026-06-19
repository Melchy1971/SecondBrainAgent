# Failure Modes

## Falsche Klassifikation
Ursache: regelbasierte Heuristik.
Gegenmaßnahme: Review Queue prüfen.

## Doppelte Notizen
Ursache: Cache-Reset oder veränderte Quelldatei.
Gegenmaßnahme: Duplicate Report prüfen.

## Zu viele Tags
Ursache: Keyword-Regeln zu breit.
Gegenmaßnahme: `secondbrain/tags.py` anpassen.

## Graph-Rauschen
Ursache: generische Backlinks.
Gegenmaßnahme: Tag- und Link-Regeln härten.

## Sync-Konflikte
Ursache: mehrere Sync-Systeme parallel.
Gegenmaßnahme: Konfliktdateien behalten, Review Queue erzeugen.
