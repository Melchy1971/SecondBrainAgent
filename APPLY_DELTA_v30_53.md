# APPLY DELTA v30.53

## Einheitliche Import-Normalisierung

- Alle Provider verwenden ausschließlich `StreamingImportService`.
- Kanonisches Modell: `Conversation`, `Message`, `Attachment`, `Source`, `Metadata`.
- Unterstützte Provider: ChatGPT, Claude, Gemini, Perplexity, LibreChat, AnythingLLM, OpenWebUI und OpenAI Export.
- Der alte eigenständige Perplexity-ZIP/Markdown/Semantic-Pfad wurde entfernt.
- JSON, JSONL, NDJSON, Markdown, Text, HTML und ZIP bleiben Streaming-Eingaben der Enterprise Engine.

## Prüfung

```powershell
.\.venv\Scripts\python.exe -m compileall -q secondbrain modules tests
.\.venv\Scripts\python.exe -m pytest -q
```
