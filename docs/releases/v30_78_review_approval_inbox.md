# Review- und Approval-Inbox: Ende-zu-Ende-Gate

Stand: 10. Juli 2026

## Ergebnis

Das neue Kommando `python launcher.py review-approval-gate` prüft den produktiven Review-/Approval-Datenfluss headless und ohne den Repository-Runtimezustand zu verändern. Das aktuelle Ergebnis ist `CONDITIONAL_PASS`: 14 von 15 Prüfungen bestehen, kein harter Blocker wurde gefunden. Die Native Approval Queue verhindert gleichzeitige, widersprüchliche Entscheidungen derzeit nicht atomar.

## Architektur

Der Launcher ruft `ReviewApprovalGate` auf. Jede Prüffolge erhält ein eigenes temporäres Projektverzeichnis und verwendet die produktiven Komponenten:

- `AgentCore`, `SafeExecutor` und `MandatoryApprovalPolicy` für Planung, Pausieren und Ausführung.
- `AgentPlanStore` und `NativeApprovalQueue` für persistente Plans und Approvals.
- `AgentApprovalService` für Approve, Reject, Defer und Audit.
- `ApprovalInboxViewModel` für die headless Prüfung der nativen Inbox-Anzeige und der kontrollierten Fehlerzustände.

Das Gate schreibt keine Approval-, Plan- oder Review-Daten in `runtime/` des Repositories. Temporäre Gate-Daten werden nach dem Lauf entfernt. Die JSON-Ausgabe folgt dem Schema `secondbrain.review_approval_gate.v1` und enthält Einzelchecks, Zusammenfassung, Blocker und Warnungen.

## Zustandsmodell

| Ausgang | Entscheidung/Aktion | Ergebnis |
| --- | --- | --- |
| `pending` | approve | `approved` |
| `pending` | reject | `rejected`, Plan beendet |
| `pending` | defer | `deferred`, Plan bleibt pausiert |
| `deferred` | approve/reject | `approved` beziehungsweise `rejected` |
| `approved` | Resume und erfolgreiche Toolausführung | `executed`, Step `completed` |
| `waiting_for_approval` | Neustart | Approval und Plan bleiben erhalten |

Ein erneuter Resume-Aufruf führt einen bereits abgeschlossenen Step nicht nochmals aus. Normale Low-Risk-Tools laufen ohne Queue-Eintrag direkt durch.

## Sicherheitsregeln

Das Gate klassifiziert die folgenden Befunde zwingend als `BLOCKED`:

- Toolausführung ohne erforderliche Freigabe.
- fehlender Entscheidungs-/Ausführungsaudit.
- doppelte Ausführung eines genehmigten Steps.
- Secret-Leak in Queue-, Plan-, ViewModel- oder Gate-Daten.
- Verlust eines offenen Approvals nach Neuinitialisierung der Runtime-Komponenten.

Delete, Send und External Write werden auch bei `requires_approval=False` blockiert. Sensitive Felder des `ToolInputSchema` müssen als `***` persistiert und angezeigt werden. Beschädigte Queue-Zeilen führen im ViewModel zu einem kontrollierten Fehlerzustand statt zu einem GUI-Absturz.

Verdikte:

- `PASS`: alle 15 Prüfungen bestanden.
- `CONDITIONAL_PASS`: kein harter Sicherheitsblocker, aber mindestens eine nicht blockierende Lücke.
- `BLOCKED`: mindestens eine der oben genannten Sicherheitsgarantien ist verletzt oder das Gate selbst kann nicht kontrolliert ausgeführt werden.

## Bekannte Grenzen

1. `NativeApprovalQueue.transition()` liest, validiert und ersetzt die Queue-Datei ohne pro Queue geteilten Lock oder Compare-and-swap. Im deterministischen Paralleltest wurden Approve und Reject beide akzeptiert (`accepted=2`, `conflicts=0`). Deshalb lautet das aktuelle Gate-Ergebnis `CONDITIONAL_PASS`. Für `PASS` ist eine atomare Statusvorbedingung über Prozess- und Threadgrenzen erforderlich.
2. Das Gate prüft die bestehende Tk-freie ViewModel-Schicht. Rendering, Fokus, Dialoginteraktion und Plattformverhalten der realen Tk-Oberfläche bleiben Aufgabe eines separaten Desktop-Smoke-Tests.
3. Das Gate validiert lokale Persistenz und Neustart durch Neuinstanziierung. Prozessabstürze exakt während eines Dateisystem-Replace werden nicht per Fault Injection simuliert.
4. Die vollständige Repository-Suite enthält externe und optionale Integrationspfade. Ihr Ergebnis ist daher getrennt vom Review-/Approval-Gate zu bewerten.

## Rollback

Der Rollback besteht aus dem Revert der fünf Dateien dieses Changes: Launcher-Dispatch, Gate-Modul, beide Testmodule und diese Release-Notiz. Es gibt keine Datenmigration und keine Änderung am persistenten Queue-Schema. Da das Gate ausschließlich temporäre Runtime-Verzeichnisse nutzt, müssen keine Gate-Daten bereinigt werden.

## Testresultate

Ausgeführt am 10. Juli 2026:

| Kommando | Ergebnis |
| --- | --- |
| `python launcher.py review-approval-gate` | `CONDITIONAL_PASS`, 14 bestanden, 1 conditional, 0 blocked |
| `pytest -q tests/test_review_approval_e2e.py` | 3 passed |
| `pytest -q tests/test_review_approval_security.py` | 4 passed |
| `pytest -q` | zweimal nach 121,6 s beziehungsweise 361,5 s bei 66 % abgebrochen; mehrere vorhandene Fehler sichtbar |
| `pytest -q --maxfail=1 --tb=short` | 434 passed, 2 skipped, 1 failed; erster Fehler: `tests/embeddings/test_live_gated.py::test_openai_live_or_skip` wegen Provider-Health `FAIL` statt `PASS` |

Die fokussierten Review-/Approval-Tests sind vollständig grün. Die Vollsuite ist nicht grün bestätigt; der zuerst reproduzierbare Fehler betrifft den externen OpenAI-Live-Embedding-Healthcheck und liegt außerhalb der fünf für dieses Gate erlaubten Dateien.
