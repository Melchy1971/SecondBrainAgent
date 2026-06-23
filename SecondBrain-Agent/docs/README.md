# SecondBrain OS / Jarvis – Dokumentation v16.9

Stand: v16.9 Mobile Companion Backend

## Zielbild
SecondBrain OS entwickelt sich zu einem persönlichen Betriebssystem für Wissen, Aufgaben, Dokumente, Agenten, Automatisierung, Sprache, Mobile Companion und proaktive Entscheidungsunterstützung.

## Aktueller Reifegrad
- Infrastruktur: hoch
- Desktop-Grundlage: vorhanden
- Datenbankgrundlage: vorhanden
- Connector Framework: vorhanden, noch ohne echte API-Calls
- Dokumentenverständnis: vorhanden, OCR/PDF noch nicht produktiv
- Multi-Agent Runtime: vorhanden, noch deterministisch
- Knowledge Graph: vorhanden, noch SQLite/Neo4j-Export
- Langzeitgedächtnis: vorhanden
- Hybrid RAG: vorhanden, noch mit Pseudo-Embeddings
- Realtime Voice: vorhanden, noch ohne echtes Mikrofon/STT/TTS
- Mobile Companion: Backend vorhanden, keine native App

## Wichtig
Die Releases v16.0 bis v16.9 sind als modulare Codepakete entstanden. Für ein produktives Gesamtsystem müssen sie in einen gemeinsamen Hauptbranch integriert werden.

## Aktueller Startpunkt

Alle lokalen Befehle aus dem Projektordner starten:

```powershell
cd H:\SecondBrainAgent\SecondBrain-Agent
```

Basisprüfung:

```powershell
python launcher.py health
```

Menü:

```powershell
python scripts\menu.py
```

Jarvis HUD:

```powershell
python scripts\start_hud.py
```

Browser: `http://127.0.0.1:8851`

Einfaches Web-Dashboard:

```powershell
python scripts\web_dashboard.py
```

Browser: `http://localhost:8765`

Weitere Startbefehle: `docs\04_STARTBEFEHLE.md`.
