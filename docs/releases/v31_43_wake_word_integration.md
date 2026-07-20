# v31.43 Wake Word Integration

Die lokale Wake-Word-Runtime ist jetzt mit der nativen Desktop-App und dem System Tray verbunden.
Sie bleibt standardmäßig aus und kann über `SECONDBRAIN_WAKE_WORD_ENABLED=true` oder das Tray-Menü
„Zuhören umschalten“ aktiviert werden.

Akzeptiert die Runtime ein Wake Word, startet sie genau eine kurze lokale Befehlsaufnahme. TTS,
Mute und Cooldown bleiben vorgeschaltet. Beim kontrollierten App-Ende wird der Listener-Thread vor
Tray und Fenster gestoppt. Fehler oder fehlende Mikrofone blockieren den Desktopstart nicht.
