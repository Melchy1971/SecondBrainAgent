# v30.64 – Agent Memory Injection

## Zweck

Agenten nutzen Memory gezielt, begrenzt und nachvollziehbar: relevante Erinnerungen mit Quelle, Confidence, Aktualität und Konflikten – unter harten Regeln (keine Secrets, Privacy Mode, Tokenbudget, Quellenpflicht).

## Wiederverwendete Bestandsobjekte

Keine zweite Memory Engine. Die Schicht liest die bestehende
`secondbrain.agent.memory` (`MemoryRecord`, `create_memory_record`,
`InMemoryMemoryStore` mit `list`/`search`). Records werden nicht dupliziert oder
neu gespeichert; die Injektion arbeitet ausschließlich lesend darauf.

## Neue Komponenten

Modul: `secondbrain/agent/memory_injection/`

| Klasse | Datei | Aufgabe |
|--------|-------|---------|
| `MemoryQuery` | `models.py` | Anfrage + Constraints (Workspace, Limit, Privacy, Budget, Quellenpflicht) |
| `MemoryEvidence` | `models.py` | eine injizierte Erinnerung (Quelle, Confidence, Aktualität, Relevanz) |
| `MemoryContext` | `models.py` | Ergebnis: Evidenzen, Quellen, Ausschlüsse, Konflikte, Budget |
| `MemoryBudget` | `budget.py` | Token-Zählung (~4 Zeichen/Token), harte Obergrenze |
| `MemoryRanking` | `ranking.py` | Relevanz + Aktualität → Confidence, deterministisch |
| `MemoryConflictDetector` | `conflicts.py` | Widersprüche (claim_key/value + Negations-Heuristik) |
| `MemoryInjector` | `injector.py` | Orchestrierung `preview`/`inject` |
| `MemoryInjectionAudit` | `audit.py` | Audit-Trail (JSONL) |

## Pipeline (Reihenfolge = Sicherheitspriorität)

Kandidaten → **Secrets raus** → **Privacy Mode raus** → **Quellenpflicht** → Ranking → Relevanz-Untergrenze → Tokenbudget + Count-Limit → Konflikterkennung → `MemoryContext`.

## Regeln

- **Secrets niemals injizieren** – erkannt über Metadaten-Flag, sensible Metadaten-Keys, Tags (`secret`, `password`, …) und Textmuster (`sk-…`, AWS/GitHub-Keys, PEM-Key, `password=…`, lange Hex-Blobs). Ausschluss unabhängig von Query und Modus. Bewusst streng (lieber over-excludieren).
- **Privacy Mode erzwingen** – schließt `visibility=private`, `private/personal`-Tags und `private`-Metadaten aus.
- **Tokenbudget beachten** – `MemoryBudget` deckelt die injizierten Tokens; Überschuss wird als `token_budget` ausgeschlossen. Zusätzlich `limit` als Anzahlgrenze.
- **Quellenpflicht** – jede Evidenz trägt eine Quelle. Bei `require_source=True` werden Records ohne explizite `metadata.source` ausgeschlossen (`no_source`); sonst wird `memory:<id>` synthetisiert.

## Agenten erhalten

Pro `MemoryEvidence`: `text`, `source`, `confidence` (0–1), `recency_days`, `relevance`, `score`, `tokens`, `scope`, `visibility`. Plus auf Kontextebene: `sources`, `exclusions` (mit Grund), `conflicts`, `budget`.

## Launcher-Kommandos

```
python launcher.py agent-memory-preview --query TEXT [--memories PATH] [--workspace ID] [--limit N] [--budget TOKENS] [--privacy] [--require-source]
python launcher.py agent-memory-inject  (wie preview) [--actor NAME] [--agent-id ID]
python launcher.py agent-memory-audit   [--agent-id ID] [--limit N]
```

`--memories` ist eine JSON-Liste von Records (`text`, `scope`, `visibility`, `workspace_id`, `tags`, `metadata`). `preview` schreibt kein Audit, `inject` schon.

## Tests

- `test_memory_injection.py` – Ranking, Quellen, Confidence, Relevanzausschluss, Workspace, Audit (nur bei inject).
- `test_memory_budget.py` – Token-Schätzung, Budget-Deckel, Count-Limit.
- `test_memory_privacy.py` – Secrets nie injiziert (Flag/Tag/Textmuster), Privacy-Mode-Ausschlüsse.
- `test_memory_conflicts.py` – claim_value-Mismatch, Negations-Heuristik, Konflikt im Kontext.

## Qualitätsnachweis

```
python -m compileall secondbrain/agent/memory_injection launcher.py
pytest tests/test_memory_injection.py tests/test_memory_budget.py tests/test_memory_privacy.py tests/test_memory_conflicts.py -q
```

Erwartung: 25 passed. Keine Regression in v30.61–v30.63. Zielinterpreter Python 3.11+.

## Hinweis

`InMemoryMemoryStore` ist nicht persistent. Die CLI lädt Records aus einer JSON-Datei (`--memories`). Für den produktiven Betrieb wird der Injector mit dem realen, befüllten Store der Anwendung konstruiert (`MemoryInjector(store)`), nicht mit einer eigenen Datenhaltung.
