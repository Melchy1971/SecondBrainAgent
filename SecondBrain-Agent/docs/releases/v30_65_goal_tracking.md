# v30.65 – Agent Goal Tracking

## Zweck

Jarvis verfolgt Ziele, Fortschritt und offene Aufgaben: Ziele mit Meilensteinen, Metriken und Evidenz, zerlegt in Pläne über den Agent Planner, Fortschritt gemessen gegen Pläne/Workflows, Berichte an Notification Center und Dashboard.

## Integration (Wiederverwendung)

| Subsystem | Quelle | Rolle |
|-----------|--------|-------|
| Agent Planner | `secondbrain/agent/planner.py` (`AgentPlanService`) | Ziel in Plan zerlegen; Fortschritt aus Plan-Schritten |
| Workflow Engine | `secondbrain/agent/workflow` (`WorkflowStore`) | optionaler Workflow-Status je Meilenstein |
| Memory | injizierbarer `memory_sink` | Ziel-Lebenszyklus-Fakten |
| Notification Center | `NotificationCenterService` | Risiko-/Abschluss-/Bericht-Meldungen |
| Dashboard | `dashboard_snapshot()` | Ziel-Aggregat für das native Dashboard |

Pläne bleiben in der bestehenden `runtime/agent/plans.json` des Planners – keine zweite Plan- oder Ziel-Ausführung.

## Neue Komponenten

Modul: `secondbrain/agent/goals/`

| Klasse | Datei | Aufgabe |
|--------|-------|---------|
| `Goal` | `models.py` | Ziel mit Meilensteinen, Metriken, Evidenz, Plan-Links |
| `GoalStatus` | `models.py` | DRAFT / ACTIVE / PAUSED / AT_RISK / COMPLETED / CANCELLED |
| `GoalMilestone` | `models.py` | Meilenstein (gewichtet, Fälligkeit, Plan-/Workflow-Link) |
| `GoalMetric` | `models.py` | Metrik (baseline/current/target, increase/decrease) |
| `GoalEvidence` | `models.py` | Beleg (Quelle, Referenz) |
| `GoalReview` | `models.py` | Berichts-Snapshot |
| `GoalStore` | `store.py` | Persistenz (goals.json, reviews.jsonl) |
| `GoalTracker` | `tracker.py` | Anwendungsservice |

## Fortschrittsmessung

Deterministische Mischung der verfügbaren Komponenten:

- **Meilensteine**: gewichteter Erledigt-Anteil.
- **Metriken**: Mittel der Einzel-Fortschritte (`(current-baseline)/(target-baseline)`, bzw. umgekehrt bei `decrease`, geклemmt auf 0–1).
- **Pläne**: Mittel über verknüpfte Pläne (abgeschlossene Schritte / Schritte, gelesen aus dem Planner).

`overall` = Mittel der vorhandenen Komponenten.

## Funktionen

- **Ziel erstellen** – `create_goal(...)`.
- **Ziel in Pläne zerlegen** – `decompose()` erzeugt über den Planner einen Plan und je Schritt einen Meilenstein.
- **Fortschritt messen** – `measure_progress()` → `overall` + Komponenten.
- **Offene Risiken anzeigen** – `risks()`: überfällige Meilensteine, überschrittenes Zieldatum, nicht erreichte Metriken, pausiert.
- **Ziel pausieren** – `pause()`/`resume()`.
- **Ziel abschließen** – `close()` (verlangt 100 % oder `force`), benachrichtigt + Memory.
- **Zielbericht erzeugen** – `report()` schreibt `GoalReview`, setzt Status (AT_RISK bei Risiken, sonst ACTIVE), benachrichtigt + Memory.

## Launcher-Kommandos

```
python launcher.py goal-create --title TEXT [--metric name:target[:current[:direction]]]... [--milestone TITLE]... [--decompose]
python launcher.py goal-list
python launcher.py goal-show   <goal_id>
python launcher.py goal-update <goal_id> [--metric name=value] [--complete-milestone ID] [--add-milestone TITLE] [--status pause|resume|cancel] [--decompose] [--evidence NOTE]
python launcher.py goal-report <goal_id>
python launcher.py goal-close  <goal_id> [--force]
```

## Tests

- `test_goal_tracking.py` – Erstellen, Zerlegen, Meilensteine, Lebenszyklus, Risiken, Dashboard.
- `test_goal_metrics.py` – Metrik-/Meilenstein-Progress, Komponenten-Blend, Plan-Fortschritt.
- `test_goal_reporting.py` – Bericht, Persistenz, Status-Ableitung, Notification/Memory.

## Qualitätsnachweis

```
python -m compileall secondbrain/agent/goals launcher.py
pytest tests/test_goal_tracking.py tests/test_goal_metrics.py tests/test_goal_reporting.py -q
```

Erwartung: 28 passed. Keine Regression in v30.61–v30.64. Zielinterpreter Python 3.11+.

## Hinweis Dashboard

`GoalTracker.dashboard_snapshot()` liefert ein read-only Aggregat (Anzahl je Status, Durchschnittsfortschritt, At-Risk-Liste). Die Anbindung an die native Dashboard-GUI erfolgt über diesen Snapshot; es wird keine zweite Datenhaltung eingeführt.
