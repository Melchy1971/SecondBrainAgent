# APPLY DELTA v30.73

## Umfang

- Bestehende Chat-Context-Pipeline um Context-, Memory- und Source-Ranking erweitern.
- Exakte und nahe Duplikate vor der Prompt-Erstellung entfernen.
- Bestehenden `MemoryConflictDetector` zur Konfliktauflösung wiederverwenden.
- Vorhandenen `TokenBudgetManager` und `PromptAssembler` beibehalten.
- Deterministische Prompt-Komprimierung und explizite Prompt-Erweiterung bereitstellen.

## Datenfluss

`Memory + RAG -> Context Ranking -> Duplicate Removal -> Conflict Resolution -> Token Budget -> PromptAssembler`

Es entsteht keine neue Persistenz und keine zweite Retrieval-, Memory- oder Context-Pipeline.

## Pruefung

```powershell
python -m compileall .
pytest -q
```
