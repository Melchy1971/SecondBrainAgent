# v31.41 System Tray

Die native Desktop-App besitzt jetzt einen optionalen System-Tray-Adapter mit Öffnen, Status,
Mikrofon-Mute, Push-to-Talk und kontrolliertem Beenden. Bei aktivem Tray minimiert das Schließen des
Fensters die App; nur „Beenden“ fährt Tray und Desktopprozess vollständig herunter.

`pystray` und Pillow sind Teil des optionalen `desktop`-Extras. Fehlen sie, startet Jarvis weiterhin
ohne Tray im Degraded Mode und das Schließen beendet das Fenster wie bisher.
