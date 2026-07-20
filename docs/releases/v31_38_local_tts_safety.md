# v31.38 Local TTS Safety

Die native Sprachausgabe verwendet eine zentrale lokale TTS-Runtime. Während der Ausgabe wechselt
die Voice Session in `SPEAKING`; Wake Words werden in diesem Zustand ignoriert. Stimme,
Geschwindigkeit und Lautstärke sind begrenzt konfigurierbar, laufende Ausgabe kann abgebrochen und
lange Antworten werden für die Sprachausgabe gekürzt.

Als sensibel markierte Inhalte, insbesondere Mail-Inhalte, werden ohne explizites `allow_sensitive`
nicht an die TTS-Engine übergeben. Die Runtime verwendet pyttsx3/Windows SAPI lokal und hat keinen
Cloud-TTS-Fallback.
