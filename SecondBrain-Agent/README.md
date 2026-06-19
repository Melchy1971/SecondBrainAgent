# SecondBrain-Agent v9.7

Persönliches KI-Betriebssystem für Wissensmanagement, Automatisierung und Selbstoptimierung.

## Voraussetzungen

- Python 3.13+
- Windows (Pfade auf `H:\SecondBrainAgent\` ausgerichtet)

```powershell
pip install pypdf requests beautifulsoup4
```

## Schnellstart

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent

# Healthcheck
python scripts\healthcheck.py

# Interaktives Menü
python scripts\menu.py

# Hauptzyklus
python scripts\run_secondbrain_os_cycle.py
```

## Verzeichnisstruktur

```
SecondBrain-Agent/
├── config/          # Konfigurationsdateien (settings.yaml, goals.yaml, …)
├── modules/         # ~160 Module (Importer, KI-Layer, Agenten, …)
├── scripts/         # Ausführbare Skripte
├── mcp-server/      # MCP-Server für Claude Desktop
├── docs/            # Dokumentation
├── archive/         # Verarbeitete Importe
├── backups/         # Automatische Backups
└── tests/           # Tests
```

## Wichtige Skripte

| Skript | Funktion |
|--------|----------|
| `scripts\menu.py` | Interaktives Hauptmenü |
| `scripts\run_secondbrain_os_cycle.py` | Vollständiger OS-Zyklus |
| `scripts\run_v97_cycle.py` | v9.7-Zyklus |
| `scripts\healthcheck.py` | Systemstatus prüfen |
| `scripts\import_ai_exports.py` | KI-Exporte importieren |
| `scripts\import_document.py` | Dokumente importieren |
| `scripts\import_chatgpt_folder.py` | ChatGPT-Ordner importieren |
| `scripts\import_gemini_folder.py` | Gemini-Ordner importieren |
| `scripts\semantic_search.py` | Semantische Suche |
| `scripts\rag_answer.py` | RAG-Antworten |
| `scripts\create_backup.py` | Backup erstellen |
| `scripts\restore_latest.py` | Letztes Backup wiederherstellen |
| `scripts\validate_config.py` | Konfiguration validieren |
| `scripts\run_quality_gate.py` | Qualitätsprüfung |

## Import-Quellen

Dateien in die Inbox-Ordner legen, dann Menü → Import:

```
H:\SecondBrainAgent\SecondBrain-Inbox\
├── PDFs\
├── Webseiten\
├── ChatGPT\
├── Gemini\
└── Perplexity\
```

## MCP-Server (Claude Desktop)

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent\mcp-server
python server.py
```

Den Server in der Claude-Desktop-Konfiguration eintragen (`claude_desktop_config.json`). Anschließend kann Claude direkt Notizen im Vault lesen und schreiben.

## Kernmodule

| Bereich | Module |
|---------|--------|
| KI-Layer | `real_ai_layer`, `reasoning_engine_v97`, `local_llm_router`, `vector_rag` |
| Wissen | `full_knowledge_graph`, `self_improving_knowledge`, `semantic_search_engine`, `ontology_engine` |
| Agenten | `agent_orchestrator`, `agent_swarm`, `agent_memory_v2`, `agent_memory_replay` |
| Importer | `chatgpt_importer`, `gemini_importer`, `claude_importer`, `perplexity_importer`, `pdf_importer` |
| Ziele | `goal_system_v97`, `goal_engine`, `decision_engine_v2` |
| Autonomie | `autonomous_mode`, `autonomous_planner`, `autonomous_project_manager` |
| Review | `self_reflection_v97`, `weekly_review_v97`, `daily_assistant_v97` |
| Backups | `backup_engine`, `backup_verification` |

## Konfiguration

Zentrale Einstellungen in `config/settings.yaml`:

```yaml
version: 9.7.0
vault_path: H:\SecondBrainAgent\SecondBrain
safe_mode_default: true
destructive_actions_allowed: false
```

Zielkategorien in `config/goals.yaml`: Beruf, Projekte, Lernen, Gesundheit, Verein, Privat.

## Sicherheitsmodell

- Safe Mode standardmäßig aktiv
- Keine destruktiven Änderungen ohne explizite Freigabe
- Keine externen Aktionen (E-Mail, API-Calls) ohne Aktivierung
- Alle Ergebnisse als Markdown
- MCP-Server prüft alle Pfade gegen Vault-Grenze
