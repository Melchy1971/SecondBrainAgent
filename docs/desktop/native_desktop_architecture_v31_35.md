# Native Desktop Architecture v31.35

## Entscheidung

| Variante | Vorteil | Nachteil | Entscheidung |
|---|---|---|---|
| Tkinter ausbauen | vorhanden, keine Zusatzabhängigkeit | monolithisch, eingeschränkte Tray-/Accessibility-APIs | Kompatibilitätsfallback |
| PySide6/Qt | native Windows-Shell, Tray, Docking, Accessibility | optionale große Abhängigkeit | Ziel-Shell |
| Web-GUI in WebEngine | hohe Wiederverwendung der UI | Browser-Runtime und Session-Komplexität | nur optionale Einzelansichten |
| Hybrid | schrittweise Migration ohne Service-Duplikate | zwei UI-Adapter während Migration | gewählt |

Die Zielarchitektur ist eine optionale PySide6-Shell über einer gemeinsamen Action Registry und
den vorhandenen Application Services. Tkinter bleibt als degradierter Startpfad erhalten. Qt und
Audio-Engines werden erst bei Verwendung importiert; fehlende optionale Pakete verhindern den
Desktopstart daher nicht.

## Grenzen und Datenfluss

`Desktop/Web/Voice/CLI adapter -> ActionRegistry -> Policy -> Application Service -> Audit/Approval`

Die Registry beschreibt ID, Aliasse, Parameterschema, Risiko, Bestätigung, Approval, Workspace,
Handler, Verfügbarkeit und Capability-Quelle. Externe Writes werden niemals direkt vom Voice-
Parser ausgeführt. Bestätigungen und Approvals sind an einen SHA-256-Hash aus Action, Payload und
Workspace gebunden. Freie Äußerungen fallen auf `assistant.ask` zurück.

Audio bleibt lokal und flüchtig. Es gibt keinen Modelldownload und kein Cloud-STT ohne explizite
Konfiguration. Während TTS akzeptiert die State Machine kein Wake Word.
