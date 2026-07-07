# Architecture Report — SecondBrain-Agent v30.77
Stand: 2026-07-07 | Analysebasis: statische AST-Auswertung des Pakets `secondbrain` + `tests`/`modules`/`scripts`

## 1. Ist-Struktur (Fakten)
- Analysierte Python-Dateien: **1659**
- Module im Paket `secondbrain`: **1095**
- Test-Dateien: 373 | `modules/` (nicht paketiert): 90 | `scripts/`: 96
- Module mit `__main__`-Einstieg (CLI-fähig): **132**
- Module mit dynamischem Import (`importlib`/`__import__`/`import_module`/`entry_points`/`pkgutil`): **15**
- Syntax-Fehler beim Parsen: **0**

## 2. Zwei parallele Bäume (struktureller Befund)
- Kanonischer Code-Root laut Festlegung: `SecondBrain-Agent/` (enthält `secondbrain/`, `tests/`, `pyproject.toml`, `pytest.ini`).
- Oberer Baum `H:\SecondBrainAgent\` besitzt eigenen `launcher.py`, `runtime/`, `data/` — Wrapper/Vault-Ebene, kein zweiter Code-Kanon.
- Zwei verschachtelte Git-Repos: `.git` sowohl in `H:\SecondBrainAgent\` als auch in `SecondBrain-Agent/`. Delta-Manifeste liegen im oberen Repo mit Pfaden `SecondBrain-Agent/...`. Anforderung: Repo-Grenzen dokumentieren, sonst inkonsistente Historie.
- Defekt benannter Ordner `H:\SecondBrainAgent\SecondBrain-Agent` **innerhalb** von `SecondBrain-Agent/` (Windows-Pfad als Ordnername) — Kopier-/Skript-Artefakt, gehört bereinigt.

## 3. Versionierte Modul-Ketten (kritischer Befund)
Es existieren 6 Modulfamilien mit `_vNN`-Parallelständen. Entgegen der Refactoring-Annahme sind das **keine toten Duplikate**, sondern **statisch referenzierte, aufeinander aufbauende Ketten**:

| Familie | Stände | Versionen | Höchster Stand |
|---|---|---|---|
| `secondbrain.chief_of_staff` | 2 | v2, v98 | `chief_of_staff_v98` |
| `secondbrain.connectors` | 2 | v13, v95 | `connectors_v95` |
| `secondbrain.digital_twin` | 4 | v2, v5, v9, v113 | `digital_twin_v113` |
| `secondbrain.event_bus` | 2 | v95, v121 | `event_bus_v121` |
| `secondbrain.launcher_runtime` | 17 | v108, v111, v112, v113, v114, v115, v116, v117, v118, v119, v120, v121, v122, v123, v124, v125, v126 | `launcher_runtime_v126` |
| `secondbrain.workflow_engine` | 2 | v9, v112 | `workflow_engine_v112` |

Beispielhaft belegt: `launcher_runtime_v111` importiert `launcher_runtime_v108`; `launcher_runtime_v126` importiert `launcher_runtime_v125`; `module_registry.py` importiert `launcher_runtime_v125`; `launcher_runtime_v120` importiert `SecondBrainLauncherV119`. Die gesamte 17-gliedrige Kette v108→v126 ist damit lauffähig eingebunden.

**Konsequenz:** Löschen älterer `_vNN`-Stände bricht die Importkette. Konsolidierung ist nur über einen kontrollierten Umbau möglich (Fassade auf höchsten Stand, `legacy_main`-Delegation entfernen, Kette schrittweise zusammenführen), **nicht** über pauschales Entfernen. Das ist ein eigenes Release, kein Aufräum-Nebenprodukt.

## 4. Dynamisches Laden (Kopplungs-/Analyse-Risiko)
- `module_registry.py` als zentrale Registrierungsstelle, dazu 15 Module mit dynamischem Import.
- `ConnectorRegistry` ist in 4 Modulen definiert; Connectoren (`github_connector`, `google_calendar_connector`, `google_drive_connector`, …) besitzen **keinen statischen Importeur** und werden mit hoher Wahrscheinlichkeit über Registry-/Verzeichnis-Scan geladen.
- **Folge für dieses Refactoring:** statische Orphan-Erkennung unterschätzt die tatsächlichen Referenzen systematisch. Jeder Entfernungskandidat ist nur unter grünem Live-/Test-Lauf belastbar (siehe Release-Readiness-Report).

## 5. Duplizierte Klassennamen (84 Namen mehrfach definiert)
Gleichnamige Klassen in ≥2 Modulen (nicht zwingend identischer Code — teils bewusste Layer-Varianten, teils echte Duplikate):

| Klasse | Definitionen |
|---|---|
| `Handler` | 8 |
| `JsonStore` | 7 |
| `ConnectorRegistry` | 4 |
| `ContextBuilder` | 4 |
| `Store` | 4 |
| `AgentState` | 3 |
| `Goal` | 3 |
| `EntityExtractor` | 3 |
| `RetryPolicy` | 3 |
| `VoiceCommand` | 3 |
| `VoiceSession` | 3 |
| `VoiceCommandRouter` | 3 |
| `AgentTask` | 3 |
| `CommandPalette` | 3 |
| `NotificationCenter` | 3 |
| `MemoryExplorer` | 3 |
| `FakeNotifications` | 3 |
| `MemorySink` | 3 |
| `SearchHit` | 2 |
| `OllamaProvider` | 2 |
| `AgentStep` | 2 |
| `AgentRun` | 2 |
| `Project` | 2 |
| `JsonlEventStore` | 2 |
| `EventBus` | 2 |

Top-Fälle mit hoher Duplikatvermutung: `Handler` (8), `JsonStore` (7), `ConnectorRegistry` (4), `ContextBuilder` (4), `Store` (4). Anforderung: pro Klassenname prüfen, ob gemeinsame Basis extrahierbar ist; `JsonStore`/`Store` sind Kandidaten für eine einzige `secondbrain.storage`-Implementierung.

## 6. Empfehlung (Architektur)
1. Zwei-Baum-/Doppel-Git-Situation dokumentieren und Verantwortlichkeit je Repo festlegen.
2. Defekt benannten Ordner entfernen.
3. `_vNN`-Ketten je Familie als eigenes Konsolidierungs-Release planen (nicht in v30.77 löschen).
4. `JsonStore`/`Store`/`Handler`-Duplikate auf gemeinsame Basis führen.
5. Statische Orphans (Report 04) nur nach grünem Windows-Testlauf quarantänisieren.
