# Lasttests v30.98 – Delta über bestehendem Perf-Harness

## Bestandsaufnahme

Vorhanden auf `main` (nicht neu gebaut): `SecondBrain/perf/harness.py`,
`registry.py`, `regression.py` (Baseline-Vergleich), `history.py`, `report.py`;
zusätzlich `rag/load_test.py`, `ga/performance_suite.py`, `tests/test_perf_framework.py`.

## Delta

Neu: `SecondBrain/perf/load_test.py` – Last-/Skalierungs-/Dauertest-Layer über
dem Harness. Enthält:

- Reproduzierbare Profile `small` / `medium` / `large` (Dokumente, Chunks,
  E-Mails, parallele Jobs/Suchen, Dateigröße, Dauer) gemäß Spec.
- `deterministic_dataset(profile, seed)` – seed-stabile, als `synthetic`
  markierte Testdaten (nie Produktionsdaten).
- `percentiles` (p50/p95/p99), `classify_bottleneck` über die 11 Kategorien
  (cpu, memory, disk, database, network, provider, lock_contention, queue, gui,
  parser, embedding).
- `LoadRun` – Checkpoints, kontrollierter Abbruch (`abort_if`), Teilreport;
  Report enthält nur Metriken, nie Dokumentinhalt (content-tragende Keys werden
  entfernt).
- `run_load_gate` – benotet PASS/CONDITIONAL_PASS/BLOCKED. BLOCKED bei
  Datenverlust, OOM, Deadlock, doppelter Ausführung, GUI-Freeze, DB-Korruption,
  Suchfehlerquote/p95 über Grenze, unbegrenztem Queue-Wachstum;
  CONDITIONAL_PASS bei Provider-Limitierung, Perf-Warnung oder Baseline-
  Regression. Baseline-Vergleich nutzt das bestehende `perf.regression.compare_runs`.

Tests: `tests/test_perf_load_test.py` (11 grün) – deckt alle 8 Abnahmekriterien
ab: reproduzierbar, kontrollierter Abbruch, Checkpoints, keine Produktionsdaten,
Baseline-Vergleich, Bottleneck-Klassifikation, Report ohne Dokumentinhalt,
Gate blockt bei Datenverlust/Deadlock.

## Launcher-Anschluss

Standalone: `python -m secondbrain.perf.load_test --profile small`.

Für die exakten Kommandos in `launcher.py`:

```python
sub.add_parser("load-test").add_argument("--profile", choices=["small","medium","large"], default="small")
sub.add_parser("load-report")
sub.add_parser("load-gate")
# Dispatch: from secondbrain.perf.load_test import PROFILES, deterministic_dataset, run_load_gate
```

Bewusst nicht blind in die 1113-Zeilen-`launcher.py` geschrieben (nicht
verifizierbar hier).

## Restrisiken

1. Der Layer definiert Profile, Generatoren, Metrik-Aggregation, Bottleneck-
   Klassifikation und die Gate-Logik – die **tatsächliche Ausführung** (50 GB,
   100 parallele Suchen, Dauerbetrieb gegen echte DB) läuft auf der
   Zielmaschine. Die Verdrahtung der Profile an die realen Import-/Such-/Job-
   Pfade ist der nächste Schritt im Live-Lauf.
2. Launcher-Anschluss als Patch dokumentiert, nicht eingespielt.
3. Nur isolierte Framework-Tests hier grün; kein realer Lastlauf in dieser Session.
