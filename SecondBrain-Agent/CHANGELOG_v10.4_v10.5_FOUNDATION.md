# Changelog v10.4/v10.5 Foundation

## Neu

- Runtime Event Store für Connector- und AI-Ereignisse
- Connector Registry mit LocalJsonConnector
- Normalizer für E-Mail, Kalender und Dokumente
- ModelRouter mit offlinefähigem EchoProvider
- OllamaProvider vorbereitet
- v10.4/v10.5 Tests ergänzt
- Dokumentation für Connector Runtime und AI Runtime ergänzt

## Architekturentscheidung

Real Connectors schreiben nicht direkt in Memory, Graph oder Agenten. Alle Daten laufen zuerst als normalisierte Events durch den Runtime Event Store.

## Risiko reduziert

- Keine direkten Seiteneffekte durch Connectoren
- Keine API-Secrets im Code
- Testbare AI Runtime ohne Modellabhängigkeit
- Grundlage für spätere Permission Engine
