# SecondBrain OS v9 – Einsteiger Guide

## Zielstruktur

```text
H:\SecondBrainAgent
├── SecondBrain
├── SecondBrain-Inbox
└── SecondBrain-Agent
```

## Start

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\menu.py
```

## Wichtigste Optionen

```text
1 = Import AI Exports
3 = SecondBrain v9 Cycle
7 = Path Check v9
8 = Release Gate v9
9 = Regression Tests v9
```

## KI-Exporte importieren

ZIP-Dateien ablegen:

```text
H:\SecondBrainAgent\SecondBrain-Inbox\ChatGPT\exports
H:\SecondBrainAgent\SecondBrain-Inbox\Gemini\exports
H:\SecondBrainAgent\SecondBrain-Inbox\Perplexity\exports
```

Dann:

```powershell
python scripts\import_ai_exports.py
```

## Einzelimport

```powershell
python scripts\import_chatgpt_export.py "C:\Users\User\Downloads\chatgpt-export.zip"
python scripts\import_gemini_export.py "C:\Users\User\Downloads\gemini-export.zip"
python scripts\import_perplexity_export.py "C:\Users\User\Downloads\perplexity-export.zip"
```

## System aktualisieren

```powershell
python scripts\run_v9_cycle.py
```

## Claude MCP

```json
{
  "mcpServers": {
    "secondbrain": {
      "command": "python",
      "args": [
        "H:\\SecondBrainAgent\\SecondBrain-Agent\\mcp-server\\server.py"
      ]
    }
  }
}
```

## Prüfung

```powershell
python scripts\check_paths_v9.py
python scripts\release_gate_v9.py
python scripts\run_regression_tests_v9.py
```
