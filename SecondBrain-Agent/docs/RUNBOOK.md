# Runbook SecondBrain-Agent v2.1

## Normaler Start

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
python scripts\menu.py
```

## Pflichtprüfung

```powershell
python scripts\validate_config.py
python scripts\write_diagnostics.py
python scripts\run_tests.py
```

## Importlauf

```powershell
python scripts\run_once.py
```

## Intelligence Cycle

```powershell
python scripts\run_intelligence_cycle.py
```

## RAG Suche

```powershell
python scripts\rag_search.py "Was weiß ich über Obsidian?"
```

## Fehlerbehebung

### Problem: Vault nicht gefunden
`config/settings.yaml` prüfen.

### Problem: PDF wird nicht gelesen
`pip install pypdf`

### Problem: Webseiten werden nicht gelesen
`pip install requests beautifulsoup4`

### Problem: Datei wird nicht erneut importiert
Cache zurücksetzen:

```powershell
python scripts\reset_cache.py
```
