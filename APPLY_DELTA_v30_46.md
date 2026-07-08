# APPLY DELTA v30.46.1 - Unified Chat Engine

## Inhalt

- Erweitert den bestehenden `NativeChatService`; kein zweiter Chat-Stack.
- Erweitert den zentralen `ApplicationState`.
- Integriert Conversation Store, Memory, ausgewählte Dokumente, Hybrid Search,
  bestehende Provider, Streaming, Markdown und Citations.
- Integriert den Chat als Mittelpunkt der bestehenden AI-Workspace-Shell.
- Vereinheitlicht Native Chat, Desktop-App, Actions, Voice und Legacy-HUD auf
  `secondbrain.native.chat.ChatEngine`.
- Behält `NativeChatService` nur als öffentlichen Kompatibilitätsalias.

## Conversation-Kommandos

```bash
python launcher.py ai-chat "Frage"
python launcher.py conversation-list
python launcher.py conversation-open <uuid>
python launcher.py conversation-export <uuid> --format md
python launcher.py conversation-delete <uuid>
python launcher.py conversation-pin <uuid>
python launcher.py conversation-search "Suchtext"
python launcher.py conversation-gui
```

Runtime-Daten werden ausschließlich unter `runtime/chat/` erzeugt und sind vom
Commit ausgeschlossen.

## Akzeptanz
```bash
python launcher.py native-desktop-health
python launcher.py repo-doctor --execute-runtime-checks
python -m compileall .
pytest -q
```
