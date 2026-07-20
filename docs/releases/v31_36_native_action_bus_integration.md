# v31.36 Native Action Bus Integration

Die bestehende Tkinter-Desktop-App und ihre Mikrofoneingabe verwenden jetzt die gemeinsame
v31.35-Action-Registry. `NativeActionBus` übersetzt bestehende deutsche Befehle in Registry-Actions,
wendet Workspace-, Confirmation- und Approval-Policies an und ruft vorhandene Application Services
direkt auf. Navigation erzeugt keinen Subprozess; RAG, Import und Index-Reparatur verwenden ihre
bestehenden Python-Services.

Externe Mail- und Kalender-Schreibaktionen werden weiterhin nicht ausgeführt. Stattdessen entsteht
ein payload- und workspace-gebundener Datensatz in `NativeApprovalQueue`. Assistant- und RAG-Aufrufe
laufen aus der Tkinter-Sicht in einem Worker-Thread, damit der UI-Thread responsiv bleibt.
