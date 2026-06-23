# PATCH P2.3.1 – Document Center Foundation

## Inhalt

- Dokument-Domainmodell `DesktopDocument`
- Statusmodell `DocumentStatus`
- In-Memory `DocumentRepository`
- Filter-/Sortiermodell `DocumentFilter`
- Selektionsstatus `DocumentSelection`
- Event-Bus für Dokument-Ereignisse
- Bulk-Actions: Reindex, Delete, Archive, Move Workspace, Add/Remove Tags, Export Metadata
- JSON-Persistenz für View-/Selection-State
- Service-Fassade `DocumentService`

## Validierung

```text
7 passed in 0.27s
```

## Einbau

Delta-Inhalt in das Projekt-Root kopieren.

```powershell
python -m pytest tests/desktop/documents
```
