# Support-/Diagnosecenter v31.00 – Delta

## Bestandsaufnahme

Vorhanden auf `main` (nicht neu gebaut): `SecondBrain/support/bundle.py`
(`SupportBundle`: diagnose, health/config/runtime-snapshot, crash, logs,
system_info, provider/database_status – alle fault-isolated), `support/
redaction.py` (rekursive Secret/PII-Redaction: key- und value-basiert),
`support/center.py` (`run_support_center`, HTML), `diagnostics.py`, Test
`test_support_bundle.py`.

## Delta

Neu: `SecondBrain/support/diagnostics_delta.py` – schließt die vier fehlenden
Bausteine, ohne Bestehendes nachzubauen:

- **Redaction-Report** (`build_redaction_report`, `RedactionReport`): listet die
  entfernten Feldpfade mit Grund (`sensitive_key` / `secret_value`) – nie den
  Wert. Nutzt den bestehenden Redactor (`is_sensitive_key`, `redact_text`).
- **Stabile Fehlercodes** (`KNOWN_ERRORS`, `classify_error`,
  `detect_known_errors`): jeder Fehler erhält einen greppbaren Code
  (SB-DB-001, SB-CONN-001, …) plus Reparaturhinweis; unbekannte Fehler →
  `SB-GEN-000`. Meldungen werden vor Ausgabe redigiert.
- **Reparaturaktionen** (`RepairAction`, `REPAIR_ACTIONS`, `RepairCenter`):
  7 Aktionen; lesende laufen sofort, **schreibende/destruktive erzeugen eine
  Approval-Anfrage** (`executed=False`, `route=approval_inbox`), löschen nie
  automatisch Daten (`auto_delete=False`), jede Aktion wird auditiert.
- **Bundle-Validierung** (`validate_bundle`): scannt das Bundle vor Export auf
  Rest-Secrets/PII und blockiert bei Fund (Feldpfade, keine Werte).

Tests: `tests/test_diagnostics_delta.py` (11 grün) – deckt alle 7
Abnahmekriterien ab: Kerndaten/valides Bundle, keine Secrets (Validator blockt),
Redaction-Report zeigt Felder, defektes Modul bricht Report nicht, Reparatur
erzeugt Approval, reproduzierbare Validierung, stabile Fehlercodes.

## Restrisiken

1. Die neuen Bausteine sind isoliert getestet; die Verdrahtung an die echte
   `SupportBundle.collect()`-Ausgabe (Redaction-Report über das reale Bundle,
   Fehlercodes über echte `recent_errors`) ist im Live-Lauf zu ziehen.
2. Repair-Ausführung nach Approval (der eigentliche schreibende Schritt) läuft
   über das bestehende Approval-System und wurde hier nicht ausgeführt.
3. GUI-Anbindung (Reparatur-Buttons, Redaction-Vorschau) nutzt diese Funktionen
   als Datenquelle; die Fläche ist mit `support/center.py` zu verbinden.
