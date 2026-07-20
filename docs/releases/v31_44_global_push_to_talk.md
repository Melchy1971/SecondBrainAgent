# v31.44 Global Push-to-Talk

Die native Desktop-App unterstützt jetzt einen optionalen globalen Push-to-Talk-Hotkey. Er ist
standardmäßig deaktiviert und wird mit `SECONDBRAIN_GLOBAL_HOTKEY_ENABLED=true` aktiviert. Der
Standard ist `<ctrl>+<alt>+j`; eine alternative, validierte Kombination kann über
`SECONDBRAIN_PUSH_TO_TALK_HOTKEY` gesetzt werden.

Der Adapter registriert ausschließlich die konfigurierte Tastenkombination und protokolliert keine
Roh-Tastendrücke. Fehlt `pynput`, bleibt die App im Degraded Mode startfähig. Beim App-Ende wird der
globale Listener vor Voice-, Tray- und Fenster-Shutdown gestoppt.
