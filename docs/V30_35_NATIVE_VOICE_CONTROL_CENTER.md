# v30.35 Native Voice Control Center

Ziel: deutsche Sprachsteuerung als eigenständiges natives Kontrollmodul konsolidieren.

## Neue Befehle, die in `launcher.py` einzutragen sind

```text
voice-center-status
voice-command <text>
voice-history
voice-config
```

## Primäre Intents

| Deutsch | Intent | Aktion |
|---|---|---|
| Jarvis Status | status | native-status |
| Öffne Dokumente | open_documents | document-explorer-gui |
| Öffne Memory | open_memory | memory-explorer |
| Öffne Agenten | open_agents | agent-control-gui |
| Suche ... | search | document-explorer-search |
| Frage ... | chat_question | native-chat-ask |
| Repariere Index | index_repair | p1-vector-index-repair |
| Importiere Datei ... | document_import | document-explorer-import |

Schreibende Aktionen bleiben bestätigungspflichtig.
