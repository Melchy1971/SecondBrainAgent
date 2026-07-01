# v30.27 Native Action Bridge

## Ziel

Die native Desktop-App soll deutsche Sprachbefehle nicht nur parsen, sondern kontrolliert ausführen.

## Änderungen

- Neuer `NativeActionDispatcher`.
- Neue CLI-Befehle:
  - `python launcher.py voice-run "Jarvis Status"`
  - `python launcher.py native-action "Öffne Dokumente"`
- Mutierende Aktionen benötigen Bestätigung.
- Native App erhält Ausführen-/Bestätigt-ausführen-Schaltflächen.
- Memory-Notizen werden lokal unter `runtime/native/voice_notes.jsonl` gespeichert.
- ViewModel-Schema auf `secondbrain.native.view_model.v30_27` aktualisiert.

## Sicherheitslogik

Direkt ausführbar:

- Status
- Suche
- Frage/RAG-Antwort
- Production Gate
- Tab-Navigation

Bestätigungspflichtig:

- Dateiimport
- Vector Index Repair
- Memory-Notiz

## Validierung

```bash
pytest tests/test_v3027_native_action_bridge.py -q
python launcher.py voice-run "Öffne Dokumente" --dry-run
python launcher.py native-action "Repariere Index" --dry-run
```
