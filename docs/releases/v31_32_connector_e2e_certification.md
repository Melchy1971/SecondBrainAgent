# v31.32 – Connector E2E Certification

## Ergebnis

`python launcher.py connector-e2e-gate` führt opt-in Read- und Cursor-Smokes für
Google Gmail/Calendar sowie Microsoft Outlook Mail/Calendar aus. Das Gate
akzeptiert ausschließlich explizit markierte, separate Testkonten und verwendet
dedizierte Token-Stores.

In der aktuellen Umgebung waren keine Testkonten konfiguriert. Der sichere Lauf
ergab deshalb `CONDITIONAL_PASS`; es wurden weder Netzwerkzugriffe noch externe
Writes ausgeführt. Reale Read-, OAuth-Refresh-, Write- und Cleanup-Evidenz steht
noch aus.

## Sicherheitsvertrag

- Keine persönlichen Hauptkonten oder implizite Standard-Credentials
- Google: nur Gmail Modify und Calendar für den isolierten E2E-Lauf
- Microsoft: User Read, Mail Read/Write/Send und Calendar Read/Write
- Token nur aus expliziten E2E-Token-Stores; keine Tokens im Report
- Writes erzeugen zunächst gebundene Approval-Anträge
- Kein Auto-Approve und keine automatische Wiederholung externer Writes
- Timeout nach unklarem Send-/Create-Ergebnis muss manuell als
  `recovery_required` behandelt werden

Der aktuelle Gate-Lauf zertifiziert bei konfigurierten Konten zwei aufeinander
folgende Read-Syncs, Cursor-Persistenz und die Approval-Pflicht für Mail Send und
Calendar Create. Externe Write- und Cleanup-Smokes werden erst nach expliziter
Genehmigung ausgeführt; ohne diese Evidenz bleibt der Connector
`approval_required` und das Gesamtgate `CONDITIONAL_PASS`.

## Konfiguration

Google:

- `GOOGLE_E2E_TEST_ACCOUNT=1`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- `GOOGLE_E2E_TOKEN_STORE`

Microsoft:

- `M365_E2E_TEST_ACCOUNT=1`
- `M365_CLIENT_ID`, optional `M365_TENANT_ID`
- `M365_E2E_TOKEN_STORE`

Mit `REQUIRED_E2E_CONNECTORS=google,microsoft` können Pflichtconnectoren
festgelegt werden. Fehlende Pflichtkonfiguration, Sync-Fehler oder ein
Approval-Bypass führen zu `BLOCKED`.

Der redigierte Report liegt unter `runtime/reports/connector_e2e_gate.json` und
enthält keine Tokens, Nachrichten, Termine oder Empfängerinhalte.
