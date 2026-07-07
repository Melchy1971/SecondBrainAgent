# v30.68 – Reasoning Engine

## Zweck

Jarvis löst Probleme strukturiert – nicht nur durch Tool-Aufrufe. Eine deterministische, nachvollziehbare Reasoning-Schicht mit Chain of Thought, Tree of Thoughts, Hypothesentest, Evidenz-Ranking, Alternativen, Unsicherheiten und Konflikterkennung.

## Integration (Wiederverwendung, keine Parallelarchitektur)

- **Memory / RAG:** `EvidenceCollector` zieht Evidenz über die v30.64 `MemoryInjector` (mit Quelle, Confidence, Aktualität, Secret-/Privacy-Filter) und über eine injizierbare RAG-Suche.
- **Konflikterkennung:** wiederverwendet den v30.64 `MemoryConflictDetector` (`Evidence` ist duck-kompatibel: `memory_id`, `text`, `metadata`).
- **Agent Planner / Workflow / Goal Tracking:** die Engine ist Library-Ebene; ein Agent kann eine Reasoning-Session vor Planung/Entscheidung nutzen. Kein Launcher-Kommando (bewusst, kein GUI-/CLI-Zwang).

## Komponenten

Modul: `secondbrain/agent/reasoning/`

| Klasse | Datei | Aufgabe |
|--------|-------|---------|
| `ReasoningSession` | `session.py` | Orchestriert einen Lösungsvorgang |
| `ReasoningChain` / `ReasoningStep` | `session.py` / `models.py` | Chain (linear) und Tree (via parent_id) of Thoughts |
| `EvidenceCollector` / `Evidence` | `evidence.py` / `models.py` | Evidenz sammeln, ranken, Konflikte |
| `Hypothesis` | `models.py` | Hypothese + Test |
| `Decision` / `DecisionScore` / `Confidence` | `models.py` | Entscheidung mit Bewertung |
| `ReasoningHistory` | `history.py` | Persistenz (JSONL) |

## Unterstützte Verfahren

- **Chain of Thought (intern):** `think(...)` erzeugt interne Schritte; `public_steps()` blendet sie aus dem Ergebnis aus.
- **Tree of Thoughts:** `branch(content, parent_id, score)` + `best_branch(parent_id)` wählt den bestbewerteten Zweig.
- **Hypothesis Testing:** `hypothesize` + `link_evidence(stance)` + `test_hypothesis` → `supported` / `refuted` / `uncertain` mit Support-Score und Confidence.
- **Evidence Ranking:** nach Confidence (Aktualität als Tie-Break); Memory-Evidenz behält ihre injizierte Confidence.
- **Alternative Lösungen / Unsicherheiten / Konflikterkennung:** an jeder Entscheidung.

## Jede Entscheidung erhält

`Confidence` (Score + Level + Faktoren), `Evidence` (Liste), `Sources` (eindeutige Quellen der Stütz-Evidenz), `Alternatives` (bewertete Nicht-Gewinner), `Risk` (low/medium/high) – plus `uncertainties` und `conflicts`.

### Confidence-Faktoren

`support` (Stützungsgrad), `volume` (Evidenzmenge), `margin` (Abstand zur zweitbesten Option), `agreement` (1 − Konfliktanteil). Gewichtete Summe → Score. Risk wird aus dem Level abgeleitet und durch Konflikte oder `high_stakes` angehoben.

## Tests

- `test_evidence.py` – Sammeln (Memory-Reuse, RAG, manuell), Ranking, Secret-Ausschluss, Konflikte.
- `test_reasoning.py` – CoT intern, ToT-Best-Branch, Hypothesentest, Session-Snapshot/History.
- `test_decisions.py` – Optionswahl, alle Pflicht-Attribute, Risk bei starker Evidenz / Konflikt / high_stakes, Alternativen-Sortierung, Unsicherheiten.

## Qualitätsnachweis

```
python -m compileall secondbrain/agent/reasoning
pytest tests/test_reasoning.py tests/test_evidence.py tests/test_decisions.py -q
```

Erwartung: 22 passed. Keine Regression in v30.61–v30.67. Zielinterpreter Python 3.11+.

## Hinweis

Die Engine ist deterministisch (kein LLM-Aufruf): sie **strukturiert** den Lösungsprozess und macht ihn auditierbar. Kandidaten-Hypothesen/-Optionen und deren Evidenz liefert der aufrufende Agent (oder werden aus Memory/RAG gesammelt); die Engine sammelt, ranked, testet, bewertet und begründet die Entscheidung.
