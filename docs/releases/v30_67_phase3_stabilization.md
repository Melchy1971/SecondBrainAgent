# v30.67 – Phase 3 Stabilisierung

Ziel: Agent Framework stabilisieren und technische Schulden reduzieren. Dieser Bericht dokumentiert, was getan wurde, was **bewusst nicht** getan wurde und warum, plus die vier geforderten Berichte.

---

## Vorgehensentscheidung (wichtig)

Die Aufgabe verlangt u.a. „doppelte Agent-Klassen / Tool-Registries / Approval-Pfade entfernen". Eine Bestandsaufnahme zeigt: **jede dieser Dubletten ist noch in Benutzung** (Details unten). Blindes Löschen würde Bestandsmodule und -tests brechen. Da die vollständige Testsuite in dieser Umgebung nicht lauffähig ist (Python 3.10 statt Ziel 3.11+; `ijson`, `tkinter` fehlen), wäre destruktives Entfernen ohne grünen Volllauf ein Verstoß gegen den Standard „Abnahme erst bei fehlerfreiem Live-Lauf".

Deshalb liefert v30.67:

- **Sichere, sofort umsetzbare Cleanups** (Git-Artefakte, `.gitignore`, Kommando-Audit, Validierung).
- **Eine Dubletten-Inventur mit risikobewertetem Deprecation-Plan** statt riskanter Sofort-Löschung.
- **Keine Änderung an Bestands-Quellcode** (kein Löschen genutzter Klassen).

---

## Phase 3 Completion Report

### Durchgeführt

1. **Runtime-/Testartefakte aus Git entfernt.** 2455 fälschlich getrackte Dateien in neun `.pytest_tmp_v3045_*`-Ordnern wurden aus dem Git-Index entfernt (`git rm -r --cached`, reversibel, Arbeitsdateien bleiben). `.gitignore` (Root und `SecondBrain-Agent/`) um `.pytest_tmp*/` erweitert, damit alle Suffix-Varianten künftig ignoriert werden. Kein reales `runtime/` war getrackt (bereits ignoriert).
2. **Launcher-Kommandos geprüft.** Alle in v30.61–v30.66 ergänzten Dispatch-Ziele importieren sauber und antworten: `approval-*`, `workflow-*`, `background-agent-*`, `agent-memory-*`, `goal-*`, `agent-control-center*`, plus `ai-workspace-navigation` (agent_control registriert).
3. **Dubletten inventarisiert** (siehe unten) mit Deprecation-Plan.
4. **Validierung ausgeführt** (siehe unten).

### Validierung (in dieser Umgebung, Python 3.10 + StrEnum-Shim)

| Prüfung | Ergebnis |
|--------|----------|
| `compileall` (agent- + native-Pakete + beide launcher.py) | OK |
| `pytest` Agent-Framework-Set (v30.61–v30.66, 22 Dateien) | **170 passed** |
| RepoDoctor (gegen Repo-Root) | **ok: true** – 48 ok / 2 warning / 0 error / 1 skipped |
| Launcher-Smoke (7 Kommandogruppen) | alle ok |
| GUI-Smoke (`build_tabs`, UI-frei) | 8 Bereiche gerendert |
| Performance (Aggregator) | overview 22,6 ms / view_model 42,9 ms bei 20 Zielen |

RepoDoctor-Warnungen: (1) README.md nennt keine aktuelle Runtime-Version; (2) Cache-Artefakte vorhanden – `scripts/p0_cleanup_artifacts.py` vor Commit ausführen.

### Bewusst nicht durchgeführt

- Löschen von `ApprovalSystem`, `ApprovalStore`, `tool_registry_v121`, altem `agent/background/` oder `agent/workflow_executor.py` – alle referenziert (s. Inventur). Migration erst nach grünem Volllauf auf 3.13.

---

## Dubletten-Inventur & Deprecation-Plan

### Approval-Pfade (4)

| Implementierung | Genutzt von | Empfehlung |
|-----------------|-------------|------------|
| `native/approval.py` `NativeApprovalQueue` | planner, safety (v30.61), native/actions, task_workspace, gui/launch, Workflow/Background/Goal-Deltas | **Kanonisch – behalten.** Alle neuen Deltas standardisieren hierauf. |
| `production_core/security/approval.py` `ApprovalWorkflow` | `production_core/runtime.py` (ProductionCore) | Eigene Domäne (Production-Core). Behalten oder später auf NativeApprovalQueue bündeln. Niedriges Risiko, kein Konflikt. |
| `security_v107.py` `ApprovalStore` | `secure_agent_kernel_v107.py` | Legacy v10.7-Kernel. **Deprecate**, sobald Kernel v107 abgelöst ist. |
| `agent/approval_system.py` `ApprovalSystem` | `gates/p2_production_gate.py`, `gates/p2_completion_report.py`, `agent/workflow_executor.py` (alt), `tests/test_v211_p2_runtime.py` | **Deprecate zusammen** mit dem alten `workflow_executor.py`. |

### Tool-Registries (2)

| Implementierung | Status |
|-----------------|--------|
| `agent/tool_registry.py` `ToolRegistry` | Kanonisch (v30.60 Unified Tool Registry). |
| `tool_registry_v121.py` | v30.60 hat die alten Pfade auf **Kompatibilitätsimporte** reduziert; noch genutzt von `launcher_runtime_v121`–`v126`, swarm, desktop_os. Vollständige Entfernung blockiert, bis diese Runtimes migriert sind. |

### Workflow / Background (Konzept-Dubletten, kein echter Konflikt)

- `agent/workflow_executor.py` (Postgres-gebunden, nutzt `ApprovalSystem`) + `tests/test_v303_agent_workflow_engine.py` vs. neue dateibasierte Engine `agent/workflow/` (v30.62). Beide getestet – alt behalten, bis Postgres-Pfad migriert.
- `agent/background/` (In-Memory-Job-Manager, `tests/agent/background/…`) vs. `agent/background_agents/` (v30.63, geplante Hintergrund-Agenten). Unterschiedliche Konzepte – nicht dedupliziert.

**Empfohlene Reihenfolge (auf 3.13, mit grünem `pytest`):** 1) `security_v107`/`secure_agent_kernel_v107` ablösen → `ApprovalStore` entfernen. 2) `agent/workflow_executor.py` (alt) + `ApprovalSystem` + `test_v303` migrieren auf v30.62-Engine. 3) `launcher_runtime_v12x` auf `agent/tool_registry` migrieren → `tool_registry_v121` entfernen. 4) `agent/background` auf `background_agents` migrieren oder als Legacy markieren.

---

## Known Limitations

- **Testumgebung ≠ Ziel:** Validierung lief unter Python 3.10 mit einem nicht-committeten `StrEnum`/`datetime.UTC`-Shim; Ziel ist 3.11+ (Repo nutzt `enum.StrEnum`). `ijson` und `tkinter` fehlen im Sandbox → `importing/streaming`, GUI-Tk-Tests und das `imports`-Workspace-Modul sind hier nicht ausführbar (auf 3.13 mit Deps vorhanden).
- **Memory-Injection (v30.64):** Ranking/Konflikte sind heuristisch (Term-Overlap, Negation), nicht semantisch; Secret-Detektor ist bewusst streng (lange Hex-Blobs → mögliche Fehlausschlüsse).
- **Background Agents (v30.63):** kein eingebauter Daemon; `run_due` muss extern getaktet werden. Monitor-Handler für RAG/Quality/Memory sind flach/konfigurierbar, nicht an die realen Systeme gebunden.
- **Agent Control GUI (v30.66):** Aggregator ohne Caching – Kosten wachsen mit Anzahl Ziele/Pläne (view_model liest je Bereich neu). Für hunderte Ziele Caching nötig.
- **Goal Tracking (v30.65):** Fortschritt ist deterministische Mischung, keine gewichtete Priorisierung zwischen den Komponenten.

## Remaining Risks

- **Mount-Truncation:** In dieser Umgebung schnitten Datei-Edits mehrfach Dateien am Ende ab (CRLF/Netz-Mount). Alle betroffenen Dateien wurden repariert und per Compile+Test verifiziert. **Vor Commit die Git-Diffs prüfen**, besonders `launcher.py` und `ai_workspace/service.py`.
- **Gestagte Löschungen:** 2455 Dateien sind als Deletions gestaged. Vor Commit `git status` prüfen; die Arbeitsdateien bleiben auf Platte.
- **Koexistierende Dubletten:** Vier Approval-Pfade und zwei Tool-Registries bestehen weiter (bewusst). Verwechslungsrisiko bis zur Migration – Deprecation-Plan befolgen.
- **Kein Volllauf:** `pytest -q` über die **gesamte** Suite wurde hier nicht ausgeführt (Deps). Verbindlicher Nachweis nur auf 3.13.

## Phase 4 Readiness

- Das Agent-Framework v30.61–v30.66 ist sauber geschichtet: Safety/Approval → Workflow-Engine → Background Agents → Memory-Injection → Goal Tracking → native Agent-Control-GUI. Jede Schicht verwendet die darunterliegende wieder (keine Parallel-Engines) und ist grün (170 Tests).
- **Vor Phase 4 empfohlen:** (1) `pytest -q` vollständig auf 3.13 grün fahren; (2) `scripts/p0_cleanup_artifacts.py` + den gestageten Untrack committen; (3) Deprecation-Plan Schritt 1–2 umsetzen; (4) Background-Scheduler und reale Memory-/RAG-Anbindung nachrüsten.
- Bei erfülltem (1)–(2) ist die Basis für Phase 4 tragfähig.

---

## Validierungsbefehle

```
python -m compileall .
pytest -q
python launcher.py repo-doctor --project-root .
python launcher.py agent-control-center
python scripts/p0_cleanup_artifacts.py   # Cache-Artefakte entfernen
```
