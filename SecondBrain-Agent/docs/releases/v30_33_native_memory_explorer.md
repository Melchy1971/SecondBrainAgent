# v30.33 Native Memory Explorer Center

## Ziel

Memory wird in der nativen Desktop-Anwendung als eigenständiges Explorer-Modul sichtbar. Der Stand bleibt file-backed und funktioniert vor produktiver Datenbankinitialisierung.

## Enthalten

- `MemoryExplorer` für Runtime-Memories, Voice Notes, Chat History und importierte JSONL-Memory-Dateien.
- Suche, Timeline, Favoriten, Archivieren/Wiederherstellen.
- Export nach JSON und Markdown.
- Native Tkinter-GUI.
- Launcher-Kommandos:
  - `memory-explorer-status`
  - `memory-search`
  - `memory-add`
  - `memory-timeline`
  - `memory-favorite`
  - `memory-archive`
  - `memory-restore`
  - `memory-export`
  - `memory-explorer-gui`

## Grenzen

- Kein produktiver Memory Graph.
- Keine Secret Encryption.
- Keine echte semantische Memory-Konsolidierung.
- Keine DB-Transaktionen; bewusst frühe native Runtime-Schicht.
