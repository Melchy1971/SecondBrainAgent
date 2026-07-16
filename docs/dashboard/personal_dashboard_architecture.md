# Persoenliches Jarvis-Dashboard v31.19

## Bestand

Das verbindliche Subsystem ist `SecondBrain/personal_dashboard`. Es aggregiert bereits Daily-Briefing-nahe Heute-Daten, Tasks, Kalender, Mail, Projekte, Approvals, Suggestions, Dokumente, Knowledge und Systemstatus. Fehler werden je Karte isoliert; langsame Dokumentquellen sind lazy, der letzte Workspace-Stand liegt im lokalen Cache. Drill-down, globale Suche, Command Palette und approvalpflichtige Quick Actions bestehen bereits.

Das native HUD und die vorhandenen Fachmodule bleiben Eigentümer ihrer Daten und Schreibaktionen. Das Dashboard ist eine read-only Aggregation mit kontrollierten Übergaben und wird nicht dupliziert.

## Zielarchitektur

```text
Fachservices / Runtime Snapshot / Monitoring
                 |
        parallele Source Reads
        Timeout / Cancellation
                 |
        DashboardSnapshot
     unabhaengige DashboardCards
                 |
       HUD / Native Dashboard
        Drill-down / Quick Action
```

Der Snapshot umfasst Workspace, Zeitpunkt, Heute, Tasks, Kalender, Mail, Projekte, Approvals, Reviews, Suggestions, Dokumente, Knowledge, Jobs, System Health und Source Status. Jede Karte besitzt Typ, Status, Prioritaet, Summary, Items, Quelle, Updatezeit, Deep Link, Error State und Cache-Kennzeichnung.

## Sicherheit und Fehlerisolierung

Workspace-Filter gelten vor jeder Projektion. Sichtbare Texte werden redigiert; technische IDs verbleiben ausschließlich in opaken Drill-down-Referenzen. Stacktraces und rohe Connectorfehler erscheinen nicht in der Hauptansicht. Riskante Quick Actions erzeugen Approval-Intents und werden nie direkt ausgeführt. Kritische Approval- und Security-Karten werden bei relevantem Zustand erzwungen und koennen nicht dauerhaft ausgeblendet werden.

## Performanceziele

- First Contentful Render der Kernkarten: <= 500 ms im lokalen Zielprofil.
- Vollstaendige Kernkarten: <= 1.5 s ohne externe Offline-Quellen.
- Inkrementeller Refresh einer Karte: <= 500 ms.
- Workspace-Wechsel aus Cache: <= 250 ms.

Langsame Quellen laufen parallel mit individuellem Timeout. Lazy Loading, Pagination, Request Cancellation und inkrementeller Refresh verhindern, dass eine einzelne Quelle die GUI blockiert. Cache-Daten werden sichtbar als gecacht markiert.

## Persistenz

Kartenreihenfolge, Sichtbarkeit, Standard-Workspace, Zeitraum, Dichte und bevorzugte Startseite werden workspace-/nutzergebunden gespeichert. Produktionspersistenz verwendet PostgreSQL; ein lokaler In-Memory-Modus ist nur fuer Entwicklung und Tests zulaessig.

## Implementierungsstand

- Snapshot und Kartenvertrag enthalten Reviews, Jobs, `card_type` und `is_cached`.
- Reviews und aktive beziehungsweise Recovery-Jobs besitzen eigene Karten und Drill-down-Ziele.
- `PostgresDashboardRepository` speichert versionierte, profil- und workspacegebundene Einstellungen.
- `DashboardRuntime` liest Quellen parallel, paginiert, misst Ladezeiten und isoliert Timeouts.
- Requests koennen kooperativ abgebrochen, einzelne Karten inkrementell aktualisiert werden.
- Quick Actions verwenden eine Safe-Action-Allowlist; unbekannte Aktionen sind standardmaessig approvalpflichtig.
