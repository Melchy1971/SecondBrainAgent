# Spezifikation: Workspace-Isolation mit RLS und gebundenen Repository-Methoden

Stand: 2026-07-21
Auslöser: Befund aus `tests/test_workspace_isolation_contract.py` — die Isolation
war rein anwendungsseitig, ohne Durchsetzung auf Datenbankebene.
Entscheidung des Product Owners: beides (RLS **und** gebundene Methoden).

## Ziel

Ein workspace-übergreifender Zugriff auf `task_project_records` ist auf zwei
unabhängigen Ebenen ausgeschlossen:

1. **Anwendungsebene** — Repository-Methoden binden jeden Zugriff an einen
   `workspace_id`. Gilt auf SQLite (Dev/Test) und Postgres.
2. **Datenbankebene** — Row Level Security filtert jede Zeile anhand einer
   Sitzungsvariable. Gilt auf Postgres und blockiert auch direkten SQL-Zugriff,
   der die Anwendungsschicht umgeht.

Keine der beiden Ebenen darf sich auf die andere verlassen.

## Nicht-Ziele

- Keine Änderung an der JSONL-Entwicklungsablage.
- Keine Migration bestehender Postgres-Daten — es existiert kein produktives
  Deployment mit diesem Schema (die pgvector-Migration war bis 2026-07-21 nicht
  lauffähig, siehe `pgvector_status` im Masterplan).
- Kein Umbau von `service.py`-Fachlogik; nur das Durchreichen von `workspace_id`.

## Durchsetzungsmodell

### Sitzungsvariable

```
app.workspace_id
```

Gesetzt per `SET LOCAL app.workspace_id = :workspace_id` innerhalb der
Transaktion des Repositories. `LOCAL` bindet den Wert an die Transaktion und
verhindert, dass er über Connection-Pooling in eine fremde Anfrage leckt.

### Policy

```sql
ALTER TABLE task_project_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE task_project_records FORCE ROW LEVEL SECURITY;

CREATE POLICY workspace_isolation ON task_project_records
    USING (workspace_id = current_setting('app.workspace_id', true))
    WITH CHECK (workspace_id = current_setting('app.workspace_id', true));
```

- `FORCE` unterwirft auch den Tabelleneigentümer der Policy. Ohne `FORCE`
  umginge der Migrations-Benutzer sie.
- `current_setting(..., true)` liefert bei fehlender Variable `NULL` statt eines
  Fehlers. Der Vergleich `workspace_id = NULL` ist dann niemals wahr — ohne
  gesetzten Workspace ist die Tabelle also leer, nicht offen. Fail-closed.
- `WITH CHECK` verhindert, dass ein INSERT/UPDATE eine Zeile in einen fremden
  Workspace schreibt.

### Fail-closed als Kernprinzip

Fehlt die Sitzungsvariable, liefert die Datenbank keine Zeilen und akzeptiert
keine Schreibzugriffe. Ein Fehler in der Anwendungsschicht führt damit zu
Datenverlust-Vermeidung, nicht zu Datenlecks.

## API-Kompatibilität

`read`, `write`, `append` erhalten einen **optionalen** Parameter
`workspace_id`. Grund: `TaskRepository` ist ein `Protocol`, mehrere Aufrufer
existieren. Ein Pflichtparameter bräche sie alle auf einmal.

Übergangsregel:

- `workspace_id` gesetzt → Sitzungsvariable wird gesetzt, RLS greift.
- `workspace_id` fehlt → Verhalten wie bisher, aber eine Warnung wird protokolliert.
- Umgebungsvariable `TASK_REPOSITORY_REQUIRE_WORKSPACE=1` → fehlender
  `workspace_id` wirft `TaskRepositoryError`. Für Produktion vorgesehen.

Damit bleibt der bestehende Code lauffähig, während der neue Pfad erzwingbar ist.

## Phasen

**Phase 1 — Primitive (dieses Paket)**
`SecondBrain/storage/workspace_context.py` (neu): SQL-Erzeugung für SET/RESET
und Policy, ohne Datenbankabhängigkeit unit-testbar.
`tests/test_workspace_context.py` (neu).

**Phase 2 — Repository-Bindung**
`SecondBrain/tasks/repository.py`: RLS in `ensure_schema`, `SET LOCAL` in
`_transaction`, optionaler `workspace_id` an `read`/`write`/`append`.

**Phase 3 — Service-Threading**
`SecondBrain/tasks/service.py`: `workspace_id` an `_read`/`_write`/`_append`
durchreichen. Reine Weiterleitung, keine Fachlogikänderung.

**Phase 4 — Gate**
`SecondBrain/release/postgres_live_gate.py`: `workspace_isolation` von
`not_implemented` in eine echte Prüfung überführen — zwei Workspaces, wechselnde
Sitzungsvariable, Nachweis dass Zeilen des einen für den anderen unsichtbar sind
und ein Schreibversuch über die Grenze scheitert.

Jede Phase wird einzeln verifiziert. Der Live-Nachweis von RLS ist erst nach
Phase 4 gegen echtes Postgres möglich; die Phasen 1–3 sind statisch bzw. gegen
SQLite prüfbar.

## Grenzen

- SQLite kennt keine RLS. Dort trägt allein die Methodenbindung. Das ist
  akzeptabel, weil SQLite laut Projektregel 13 nur Dev/Test ist.
- RLS schützt `task_project_records`. Weitere workspace-behaftete Tabellen
  (Jobs, Approvals) sind nicht Teil dieses Pakets und in ihren Repositories
  bereits parameter-gebunden — der RLS-Backstop dort ist eigene Folgearbeit.
