# v31.40 Desktop Lifecycle

Die native Desktop-App schützt ihren Prozess jetzt mit einer PID-basierten Single-Instance-Sperre.
Eine aktive zweite Instanz endet kontrolliert; eine Sperre eines abgestürzten Prozesses wird sicher
übernommen. Die Sperre liegt ausschließlich unter `runtime/native` und wird beim normalen Ende
entfernt.

Fenstergeometrie und aktive Ansicht werden atomar gespeichert. Beim Start werden nur syntaktisch
und größenmäßig plausible Geometrien übernommen; korrupte Zustände verhindern den App-Start nicht.
Voice Sessions werden bewusst nicht als aktive Audiozustände wiederhergestellt.
