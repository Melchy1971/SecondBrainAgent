# APPLY DELTA v30.74

## Umfang

- Typisierte Layer: System, Workspace, Memory, Goal, Document, User und Provider Prompt.
- `FinalPromptBuilder` als zentrale Assembly-Implementierung hinter dem bestehenden `PromptAssembler`.
- Provider-Fallback fuer Modelle ohne native System-Prompt-Unterstuetzung.
- Append-only Prompt Audit ohne Prompt-Inhalte.
- Append-only Prompt History mit bestehender Secret-Redaction.
- Direkte Integration in den kanonischen `ChatEngine`-CompletionRequest-Pfad.

## Persistenz

- `runtime/chat/prompts/audit.jsonl`
- `runtime/chat/prompts/history.jsonl`

Utility-Aufrufe ohne `project_root` bleiben schreibfrei.

## Pruefung

```powershell
python -m compileall .
pytest -q
```
