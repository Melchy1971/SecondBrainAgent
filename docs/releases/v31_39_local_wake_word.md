# v31.39 Local Wake Word Runtime

Die native Voice Session besitzt jetzt eine lokale, standardmäßig deaktivierte Wake-Word-Runtime
für `Jarvis`, `Hey Jarvis` und `SecondBrain`. Sie läuft in einem stoppbaren Daemon-Thread mit
konfigurierbarem Poll-Intervall und Cooldown gegen Mehrfachaktivierungen.

Während TTS oder im Zustand `MUTED` wird keine Aktivierung akzeptiert. Die Runtime speichert keine
Audiodaten und kennt keine Cloud-Schnittstelle; konkrete lokale Audio-/Phrase-Provider werden über
eine kleine injizierbare Schnittstelle angebunden. Fehler eines fehlenden Mikrofons versetzen die
Desktop-App nicht in einen Crash-Zustand.
