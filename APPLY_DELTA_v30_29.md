# Apply Delta v30.29 — Native Chat Center

## Inhalt

Dieses Delta erweitert die native Anwendung um ein lokales Chat Center.

## Dateien kopieren

Kopiere alle Dateien aus dem ZIP in das Projektverzeichnis und überschreibe vorhandene Dateien.

## Validierung

```bash
python launcher.py native-chat-status
python launcher.py native-chat-ask "Was ist der aktuelle Projektstatus?"
python launcher.py native-chat-search "PostgreSQL pgvector"
python launcher.py voice-run "Frage was fehlt noch"
pytest tests/test_v3029_native_chat_center.py -q
```

## Neue Runtime-Datei

```text
runtime/native/chat_history.jsonl
```

Nicht ins Git aufnehmen.
