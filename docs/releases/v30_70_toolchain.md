# v30.70 – ToolChain

## Zweck

Zusammengesetzte Tool-Workflows mit Kontrollfluss und Resilienz: bedingte Schritte, Schleifen, parallele Schritte, Retry, Fallback, Rollback, Fehlerbehandlung – plus eine visuelle Darstellung. Tools laufen über die bestehende `ToolRegistry` – kein zweiter Tool-Executor.

## Wiederverwendung

`ToolChainExecutor.invoke_tool` ruft `ToolRegistry.run(name, inputs, approved)` (v30.60 Unified Tool Registry). Für Tests kann ein `tool_runner(name, inputs)` injiziert werden.

## Komponenten

Modul: `secondbrain/agent/toolchain/`

| Klasse | Datei | Aufgabe |
|--------|-------|---------|
| `ToolChain` | `chain.py` | Fluent-Builder / Container |
| `ToolChainExecutor` | `executor.py` | Ausführung mit Kontrollfluss + Recovery |
| `ToolStep` / `ConditionalStep` / `LoopStep` / `ParallelStep` | `models.py` | Schritttypen |
| `ChainContext` / `ChainRun` / `StepResult` / `RetryPolicy` | `models.py` | Kontext, Ergebnis, Policy |
| `VisualWorkflow` | `visual.py` | Mermaid + ASCII |

## Kontrollfluss

- **Conditional Steps:** `conditional(condition, then, else)`. Bedingung als Callable `(ctx)->bool` oder Spec `{"var","op","value"}` (`==`, `!=`, `>`, `<`, `in`, `truthy`, …).
- **Loops:** `loop_while(condition, body, max_iterations)` und `foreach(items_var, body)`. `max_iterations` verhindert Endlosschleifen.
- **Parallel Steps:** `parallel([branch1, branch2, …])`. Zweige sind unabhängig; ein Fehler in einem Zweig lässt den Parallel-Schritt fehlschlagen. (Deterministisch sequenziell ausgeführt; Semantik = unabhängig.)

## Resilienz / Error Handling

- **Retry:** `max_attempts` je ToolStep.
- **Fallback:** alternativer Step bei erschöpften Retries.
- **Rollback:** je ToolStep ein `rollback_tool`; bei Chain-Fehler werden abgeschlossene Schritte in **umgekehrter** Reihenfolge kompensiert.
- **Error Handling:** ein fehlgeschlagener Schritt (ohne Recovery) setzt `ChainRun.status = failed`, protokolliert den Fehler und löst Rollback aus (`rollback_on_error`, Standard an).

## Kontext & I/O

`ChainContext` hält Variablen; `output_var` legt das Tool-Ergebnis ab; Inputs mit `"$var"` werden aufgelöst. So verketten Schritte Daten.

## Visual Workflow

`chain.visualize()` liefert `VisualWorkflow` mit `.ascii()` (eingerückter Baum) und `.mermaid()` (`flowchart TD`), plus `.to_dict()`.

## Tests

- `test_toolchain.py` – sequenzielle Tools, Kontext/`output_var`/`$`-Auflösung, ToolRegistry-Reuse, Visual.
- `test_toolchain_control_flow.py` – Conditional then/else/Callable, foreach, while (Terminierung + `max_iterations`), parallel (alle Zweige, Fehler).
- `test_toolchain_recovery.py` – Retry (Erfolg/erschöpft), Fallback (Recovery/propagiert), Rollback (Reihenfolge, abschaltbar), Fehlerprotokoll.

## Qualitätsnachweis

```
python -m compileall secondbrain/agent/toolchain
pytest tests/test_toolchain.py tests/test_toolchain_control_flow.py tests/test_toolchain_recovery.py -q
```

Erwartung: 20 passed. Keine Regression in v30.61–v30.69. Zielinterpreter Python 3.11+.

## Abgrenzung zur v30.62 Workflow Engine

Die Workflow Engine (v30.62) führt Agent-Pläne mit Checkpoints/Approval/Crash-Resume aus. ToolChain ist eine leichtgewichtige, in-memory Tool-Komposition mit reichem Kontrollfluss (Loops/Parallel/Fallback/Rollback) und Visualisierung. Beide nutzen dieselbe Tool-Ausführung; sie ersetzen einander nicht.
