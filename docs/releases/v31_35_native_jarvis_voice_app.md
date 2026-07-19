# v31.35 Native Jarvis Voice App

Die native Desktoparchitektur besitzt jetzt eine gemeinsame Action Registry, eine threadsichere
Voice Session State Machine, gebundene Confirmations/Approvals, Assistant-Fallback, Wake-/TTS-
Feedbackschutz und eine optionale PySide6-Shell mit Degraded Mode. Der neue Gate-Befehl schreibt
einen redigierten Bericht nach `runtime/reports/native_voice_app_gate.json`.

Die vorhandene Tkinter-App und ihre Service-Adapter bleiben kompatibel. STT/TTS-Implementierungen
sind weiterhin optionale lokale Adapter; es erfolgt kein automatischer Modelldownload.
