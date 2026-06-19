# Production v7.0

## Ziel

Aus Framework wird produktionsnahes lokales System.

## Prüfkette

```powershell
python scripts\validate_config.py
python scripts\run_tests.py
python scripts\production_gate.py
python scripts\verify_backups.py
```

## Connectoren

Produktive Connectoren sind vorbereitet, aber sicher deaktiviert, solange keine Zugangsdaten hinterlegt sind.

## KI-Layer

Ollama muss lokal laufen:

```powershell
ollama serve
```

Dann:

```powershell
python scripts\ai_review_sample.py
```

## Obsidian Plugin

Das Plugin-Gerüst muss separat gebaut und in `.obsidian/plugins/secondbrain-agent` kopiert werden.

## Web-App

Backend:

```powershell
python webapp\backend\main.py
```

Frontend:

```powershell
cd webapp\frontend
npm install
npm run dev
```
