# v30.29 Native Chat Center

## Ziel

Die native Desktop-App erhält einen lokalen Chat-Verlauf und einen Chat-Pfad ohne Web-HUD-Abhängigkeit.

## Änderungen

- `secondbrain/native/chat.py`
- `native-chat-status`
- `native-chat-ask <frage>`
- `native-chat-search <query>`
- `native-chat-clear`
- Chat-Verlauf: `runtime/native/chat_history.jsonl`
- Voice-/Action-Bridge schreibt Fragen und Suchen in den Chat-Verlauf.
- Native GUI erhält Tab `Chat`.
- Runtime ViewModel enthält `chat`.

## Akzeptanz

```bash
python launcher.py native-chat-status
python launcher.py native-chat-ask "Was ist der aktuelle Projektstatus?"
python launcher.py voice-run "Frage was fehlt noch"
pytest tests/test_v3029_native_chat_center.py -q
```
