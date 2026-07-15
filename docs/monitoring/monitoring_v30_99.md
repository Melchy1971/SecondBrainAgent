# Betriebsmonitoring v30.99 – Delta (Verbinden, nicht neu bauen)

## Bestandsaufnahme

Auf `main` bereits vorhanden (nicht angefasst): `observability/structured_log.py`,
`audit_store.py`, `health_timeline.py`, `redaction.py`, `taxonomy.py`;
`monitoring/health.py` (`HealthMonitor`, `HealthStatus` ok/warn/critical/
unavailable, Ampel, Worst-State, 12 Komponenten-Checks), `monitoring/dashboard.py`,
`monitoring/history.py`; `native/runtime_snapshot.py`; `production_core/
observability/{health,metrics}.py`; ~20 Komponenten-Health-Reports; Tests
(`test_health_monitoring.py` u.a.).

## Delta

Neu: `SecondBrain/monitoring/operations_monitor.py` – verbindet die vorhandenen
Bausteine zu einer konsistenten Betriebssicht:

- Sechs Betriebsstatus `OperationalStatus` (ready/degraded/blocked/unavailable/
  recovering/maintenance) mit `map_health_status`, das die bestehende
  Ampel-`HealthStatus` (ok/warn/critical/unavailable) darauf abbildet.
- `HealthCheckResult` mit dem vollen Feldsatz: component, status, checked_at,
  latency_ms, message, metrics, blockers, warnings, remediation, correlation_id
  (+ `diagnostics`, das nur im Support Center, nicht in der Hauptansicht landet).
- `OperationsMonitor`: Checks mit **echtem Timeout** (ThreadPoolExecutor);
  **Fehlerisolation** (ein abstürzender Check → `unavailable`, Board bleibt
  funktionsfähig); Worst-State-Aggregation (neutral: unavailable/maintenance);
  Historie über die injizierte `HealthTimeline`; `acknowledge`; **Maintenance
  Mode**, der erwartete Warnungen nachvollziehbar unterdrückt (Status →
  maintenance, Grund in message); Alert-Erzeugung für unbestätigte Blocker;
  `export()` secret-frei (nutzt vorhandene `RedactionMiddleware`, Fallback
  eigener Scrubber). `recovering`-Overlay bei Übergang von blocked/unavailable
  auf ready.

Keine technischen Stacktraces und keine Secrets in der Hauptansicht; kein Health
Check löst eine schreibende Aktion aus (nur Callables, die Status liefern).

Tests: `tests/test_operations_monitor.py` (11 grün) – deckt alle 8
Abnahmekriterien ab: DB→BLOCKED, Provider→unavailable, Fehlerisolation,
Historie, Timeout, keine Secrets im Export, Reuse der Ampel-Abbildung,
Maintenance unterdrückt Warnungen nachvollziehbar.

## Restrisiken

1. `default_operations_monitor()` verdrahtet den Aggregator lazy an den echten
   `HealthMonitor` + `HealthTimeline` + `RedactionMiddleware`; dieser Live-Pfad
   (mit psutil/DB) wurde hier nicht ausgeführt – isoliert getestet ist die
   Aggregationslogik mit injizierten Checks.
2. GUI-Anbindung (Systemübersicht/Ampel/Deep-Links) nutzt `system_view()` als
   Datenquelle; die konkrete GUI-Fläche ist Bestand (`monitoring/dashboard.py`,
   `gui/system_monitor.py`) und im Live-Lauf zu verbinden.
3. Kein Launcher-Kommando ergänzt (Prompt 38 fordert keins); Aufruf über
   `default_operations_monitor().system_view()`.
