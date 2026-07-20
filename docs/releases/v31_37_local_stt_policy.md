# v31.37 Local STT Policy

Die native Mikrofoneingabe verwendet lokale Speech-to-Text-Engines in dieser Reihenfolge:
`faster-whisper`, Vosk und erst danach optionales Cloud-STT. Google Speech Recognition ist nur mit
`SECONDBRAIN_CLOUD_STT_OPT_IN=true` zulässig.

Für faster-whisper muss `SECONDBRAIN_WHISPER_MODEL_PATH` auf ein bereits vorhandenes lokales
Modellverzeichnis zeigen; für Vosk gilt entsprechend `SECONDBRAIN_VOSK_MODEL_PATH`. Es erfolgt kein Modelldownload. Temporäre WAV-Daten werden nach der
Transkription auch im Fehlerfall gelöscht; dauerhaftes Roh-Audio wird nicht gespeichert.
