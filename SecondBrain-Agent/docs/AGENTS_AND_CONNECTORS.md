# Agenten, Automationen und Connectoren

## Architekturprinzip

```text
Ziel oder externes Ereignis
  -> Registry / Normalizer / Planner
  -> Policy und Risk Boundary
  -> registriertes Tool oder Workflow
  -> Verify und Audit
  -> Runtime State, Report oder Review
```

Agenten duerfen keine beliebigen Shell-Kommandos oder externen Schreibaktionen ausfuehren. Aktive Faehigkeiten muessen registriert, begrenzt und auditierbar sein.

## Agenten und Workflows

Das Repository enthaelt historische und aktuelle Foundations fuer Supervisor-, Planner-, Research-, Execution-, Review-, Memory- und Improvement-Rollen. Viele aeltere, versionierte Launcher-Oberflaechen sind nicht Teil des aktuellen Command Index.

Verbindliche Pruefung:

```powershell
python launcher.py command-index
python launcher.py module-status
python launcher.py module-health
```

Produktive LLM-Planung, echte Tool-Aufrufe, autonome Policy-Aenderungen und automatische Codeaenderungen gelten nicht als freigegeben.

## Automationen

Scheduler und Runtime-Ziele duerfen ausschliesslich registrierte Aktionen verwenden. Persistente Aufgaben brauchen nachvollziehbare Run-Historie, Retry-Regeln und eine sichere Deaktivierung. Riskante Ziele bleiben approvalpflichtig.

## Connector-Pipeline

```text
Provider API / lokaler Import
  -> read-only Adapter
  -> Normalisierung
  -> Delta Cursor und Retry
  -> Event / Connector Item
  -> RAG, Memory oder Review
```

Vorhandene Foundations decken unter anderem Gmail, Google Calendar, Google Drive, GitHub, Obsidian und Paperless ab. Die blosse Existenz eines Adapters oder OAuth-Templates ist kein Beleg fuer produktive Synchronisation.

## Sicherheitsanforderungen

- Standardmodus read-only.
- OAuth-Tokens und API-Keys nie im Repository oder in Reports speichern.
- Token Refresh, Scopes, Delta Cursor, Backoff und Dead Letter Queue explizit testen.
- Externe Schreiboperationen nur nach sichtbarer Freigabe.
- PII und Secrets vor Audit-Ausgaben redigieren.
- Lokale HTTP-/API-Bruecken standardmaessig nur an Loopback binden.

## Offene Produktionsschritte

1. Echten OAuth-Browserflow und verschluesselten Token Store bereitstellen.
2. Read-Sync gegen Zielkonten end-to-end validieren.
3. Retry-, Rate-Limit- und Refresh-Fehler testen.
4. Approval und Audit fuer Write-Szenarien abnehmen.
