# SecondBrainAgent v9.1.1 Pathfix Production

## Korrigierte Zielstruktur

```text
H:\SecondBrainAgent
├── SecondBrain
├── SecondBrain-Inbox
└── SecondBrain-Agent
```

## Korrigiert

- ChatGPT Importer
- Gemini Importer
- Perplexity Importer
- MCP Server
- Claude Desktop Config
- v9 Cycle
- API Gateway
- Release Gate
- Config YAMLs
- Dokumentation

## Prüfen

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\check_paths_v9.py
```

## Gemini Import

```powershell
python scripts\import_gemini_export.py "C:\Users\User\Downloads\gemini-export.zip"
```

Ergebnis:

```text
H:\SecondBrainAgent\SecondBrain\05_Quellen\Gemini
```

## ChatGPT Import

```powershell
python scripts\import_chatgpt_export.py "C:\Users\User\Downloads\chatgpt-export.zip"
```

## Perplexity Import

```powershell
python scripts\import_perplexity_export.py "C:\Users\User\Downloads\perplexity-export.zip"
```
