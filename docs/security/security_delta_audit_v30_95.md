# Security-Delta-Audit v30.95

Stand: Analyse gegen Remote-`main` (`9149839`). Ziel: vorhandenen Security-Stand
gegen den aktuellen Code prüfen und ausschließlich noch offene Angriffsflächen
schließen. Kein Neubau vorhandener Subsysteme.

## Vorhandener Schutz (nicht neu implementiert)

| Schutz | Ort auf main | Abdeckung |
| --- | --- | --- |
| Gehärtetes Prompt Assembly | `secondbrain/chat/context/prompt_pipeline.py`, Gate-Check `prompt_boundary` | Dokumentinhalt kann nicht zu Systeminstruktion werden |
| Prompt-Injection-Erkennung | `SecondBrain/security_v107.py` (`PromptSanitizer`), Gate-Check `prompt_patterns` | 8 Injection-Muster erkannt und neutralisiert |
| RAG-Trust-Boundary | `secondbrain/rag/context_builder.py`, Gate-Checks `rag_injection`, `rag_trust` | untrusted → sanitized, trusted behält Label |
| Parser-Härtung | `secondbrain/document_understanding/*`, Gate-Checks `path_traversal`, `json_depth`, `zip_bomb`, `archive_traversal` | Traversal, JSON-Tiefe, ZIP-Bomben, Archiv-Traversal |
| Approval Governance | `SecondBrain/agent/safety/policy.py` (`SafetyPolicy`), `agent/approval_*.py`, `agent/safety/guard.py` | ALLOW/REQUIRE_APPROVAL/BLOCK je Risikostufe, Audit je Aktion |
| Secret Redaction | `SecondBrain/desktop/settings/security/secret_policy.py`, `agent/memory_injection/*`, `chatgpt_importer` Redaction | Secrets aus Logs/Reports/Memory |
| Review-/Approval-Release-Gate | `agent/review_approval_release_gate.py`, `launcher.py review-approval-release-gate` | Governance-Zertifizierung |
| Security-Gate (Basis) | `SecondBrain/security_gate_v3095.py`, `launcher.py security-gate` | 9 Checks (Prompt/RAG/Parser) |

## Befunde (Delta)

Legende Priorität: P0 kritisch, P1 hoch, P2 mittel. E = Eintrittswahrscheinlichkeit, S = Schadensausmaß.

### D-01 SSRF gegen interne Ziele
- Komponente: Connector Runtime / Web-Fetch (`connector_runtime/*`, `connectors/**`)
- Trust Boundary: Anwendung → externes Netzwerk, URL teils aus Dokument-/Connectordaten
- Angriffsvektor: Fetch auf `127.0.0.1`, private Bereiche, `169.254.169.254` (Cloud-Metadaten), Nicht-HTTP-Schemata, eingebettete Credentials
- Vorhandener Schutz: keine zentrale Zielklassifikation gefunden
- Verbleibendes Risiko: Zugriff auf interne Dienste/Metadaten, Credential-Leak
- E: mittel · S: hoch · Priorität: **P0**
- Betroffene Dateien: `connector_runtime/runtime.py`, `connectors/**`
- Maßnahme: `classify_fetch_target` / `is_safe_redirect` (blockt privat/loopback/link-local/reserved/multicast/Metadaten, Nicht-HTTP, URL-Credentials). **Umgesetzt** (`security_delta_v3095`).

### D-02 Symlink-Escape / Path Traversal jenseits `..`
- Komponente: Dateisystemzugriffe (Import, Parser, Backup)
- Trust Boundary: kontrollierte Wurzel → beliebiger Pfad via Symlink
- Angriffsvektor: Symlink innerhalb erlaubter Wurzel zeigt nach außen
- Vorhandener Schutz: Parser blockt `..`-Traversal, aber keine realpath-Containment gegen Symlinks
- E: niedrig · S: hoch · Priorität: **P1**
- Betroffene Dateien: `document_understanding/*`, Import-Pipeline
- Maßnahme: `resolve_within_root` (realpath-Containment). **Umgesetzt**.

### D-03 Log Forging
- Komponente: Structured Logging, Audit
- Trust Boundary: nutzer-/dokumentkontrollierter Wert → Logzeile
- Angriffsvektor: CR/LF/Steuerzeichen fälschen zusätzliche Logzeilen, verfälschen Audit
- Vorhandener Schutz: keine zentrale Logwert-Neutralisierung gefunden
- E: mittel · S: mittel · Priorität: **P1**
- Betroffene Dateien: Logging-Adapter, `agent/safety/audit.py`
- Maßnahme: `sanitize_log_value` (CR/LF escapen, Steuerzeichen ersetzen, Länge kappen). **Umgesetzt**.

### D-04 Übergroße CSV/XML
- Komponente: Dokumentparser
- Trust Boundary: untrusted Datei → Parser-Ressourcen
- Angriffsvektor: riesige CSV/XML (DoS); Gate prüft bisher nur JSON-Tiefe/ZIP
- Vorhandener Schutz: `json_depth`, `zip_bomb` vorhanden; CSV/XML-Größe nicht
- E: mittel · S: mittel · Priorität: **P2**
- Betroffene Dateien: `document_understanding/parsers/*`
- Maßnahme: `tabular_within_limits` (Byte-/Tiefen-/Zeilenlimits für csv/xml/json). **Umgesetzt**.

### D-05 Approval Replay
- Komponente: Approval-System
- Trust Boundary: freigegebene Aktion → erneute Ausführung
- Angriffsvektor: Wiedereinspielen einer freigegebenen (approval_id, payload_hash)-Kombination
- Vorhandener Schutz: kein Nonce-/Exactly-once-Guard im `approval_system` gefunden (grep leer)
- E: niedrig · S: hoch · Priorität: **P0**
- Betroffene Dateien: `agent/approval_system.py`, `agent/safety/guard.py`
- Maßnahme: `ReplayGuard` (exactly-once je (approval_id, payload_hash)). **Umgesetzt** (Guard); Einbindung in `commit`-Pfad = Restrisiko.

### D-06 Workspace Crossing
- Komponente: Approval / Ressourcenzugriff
- Trust Boundary: Workspace-Isolation
- Angriffsvektor: Aktor aus Workspace A greift auf Ressource aus Workspace B zu
- Vorhandener Schutz: Workspace-IDs vorhanden, aber keine zentrale Crossing-Assertion
- E: niedrig · S: hoch · Priorität: **P1**
- Betroffene Dateien: `agent/safety/guard.py`, Service-Layer
- Maßnahme: `assert_same_workspace`. **Umgesetzt** (Guard); Verdrahtung an Aufrufstellen = Restrisiko.

### D-07 Plugin-/Update-Manifest-Manipulation, unsignierte Ausführung
- Komponente: Plugin Runtime, Updatepfad
- Trust Boundary: externes Manifest → Ausführung
- Angriffsvektor: manipuliertes/unsigniertes Manifest, unbekannter Signaturschlüssel
- Vorhandener Schutz: keine zentrale Signaturpflicht im gelesenen Umfang
- E: niedrig · S: kritisch · Priorität: **P0**
- Betroffene Dateien: Plugin-Runtime, `secondbrain/update/*` (Prompt 40)
- Maßnahme: `verify_manifest_signature` (Signatur zwingend, nur vertrauenswürdige Key-IDs, HMAC-Prüfung). **Umgesetzt** als Guard; produktiver Signaturmechanismus (asymmetrisch) in Prompt 40.

### D-08 SQL-Identifier-Injection / Command Injection
- Komponente: SQL-Zugriffe, Subprozessaufrufe
- Trust Boundary: dynamischer Bezeichner / Argument → Query/Shell
- Angriffsvektor: dynamischer Tabellen-/Spaltenname, Shell-Metazeichen
- Vorhandener Schutz: parametrisierte Queries (Werte) im Repository-Layer angenommen; dynamische Identifier und Shell-Bau ungeguarded
- E: niedrig · S: hoch · Priorität: **P1**
- Betroffene Dateien: SQL-Repositories, Subprozess-Aufrufe
- Maßnahme: `safe_sql_identifier`, `contains_shell_metacharacters`. **Umgesetzt** (Guards).

## Bereits abgedeckt (kein Delta)

- Tool-Call Injection, indirekte Prompt Injection über RAG, System-Prompt-Exfiltration, gefährliche HTML/Markdown-Inhalte: durch `PromptSanitizer` + `prompt_boundary`/`rag_injection` Gate-Checks abgedeckt.
- Archive Bombs, rekursive Archive, übergroße JSON, Path Traversal (`..`): durch bestehende Parser-Checks abgedeckt.
- Externe Schreibaktion ohne Approval: durch `SafetyPolicy` + Approval-Queue abgedeckt.

## Security Policy (Phase 3)

Zentrale Entscheidungsschicht `security_delta_v3095.SecurityDecision` mit
Vertrauensstufen `trusted | untrusted | sanitized | blocked`, Risikostufen
`low | medium | high | critical` und dem geforderten Entscheidungssatz je Verdikt:
`rule_id`, `risk_level`, `reason`, `source`, `correlation_id`, `action`
(`allow|sanitize|block`), `blocked`, `sanitized`, `audit_reference`. Der
Entscheidungssatz enthält nie den inspizierten Rohwert (kein Secret-/URL-Leak).
Die bestehende `SafetyPolicy` (Aktions-Risiko/Approval) bleibt unverändert; die
neue Schicht ergänzt input-/boundary-seitige Verdikte.

## Security Gate (Phase 4)

`security_gate_v3095.run_security_gate` wird **erweitert** (kein Parallel-Gate):
die 9 Bestandschecks bleiben, `run_security_delta_checks()` hängt 8 Delta-Checks
an (ssrf, path_escape, log_forging, tabular_limits, approval_replay,
workspace_crossing, manifest_signature, injection_identifiers). `security_summary`
erhält `delta_hardening`. Gate bleibt BLOCKED (`status=FAIL`) bei jeder offenen
Lücke.

## Restrisiken

1. **Guards vs. Aufrufstellen**: SSRF-, Replay-, Workspace-, Manifest-Guards sind
   implementiert und getestet, aber die Verdrahtung an allen produktiven
   Aufrufstellen (Connector-Fetch, Approval-Commit, Plugin-/Update-Loader) ist
   in dieser Umgebung nicht ausführbar und muss im Live-Lauf verifiziert werden.
2. **DNS-Rebinding**: `classify_fetch_target` klassifiziert URL-Literale; eine
   Auflösung öffentlicher Namen auf private IPs (Rebinding) muss zur Fetch-Zeit
   erneut geprüft werden (Runtime-Aufgabe).
3. **Manifest-Signatur**: hier HMAC-basiert (deterministisch, dependency-frei);
   der produktive asymmetrische Signaturpfad kommt mit Prompt 40 (Auto-Updater).
4. **Live-Gate-Lauf**: `python launcher.py security-gate` und die
   Integrationssuiten (`tests/test_security_hardening_gate.py`,
   `test_review_approval_security.py`, `test_action_guard.py`) erfordern
   ausgecheckten `main` + volle Laufzeit (Postgres/pgvector) und wurden in dieser
   Session nicht ausgeführt. Isoliert getestet: `tests/test_security_delta_v3095.py`
   (23 grün).

## Verifikation (auf Zielumgebung auszuführen)

```
python launcher.py security-gate
python -m pytest -q tests/test_security_delta_v3095.py
python -m pytest -q tests/test_security_hardening_gate.py
python -m pytest -q tests/test_action_guard.py
python -m pytest -q tests/test_review_approval_security.py
python -m pytest -q
```
