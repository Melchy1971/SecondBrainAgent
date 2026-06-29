---
title: "5-adriges Kabel prüfen"
type: chatgpt_conversation
source: chatgpt
source_id: "6a39770e-da7c-83ed-8067-9d64a0830810"
created: 2026-06-22
tags:
  - chatgpt
  - import
---


# 5-adriges Kabel prüfen

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `6a39770e-da7c-83ed-8067-9d64a0830810`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

Wir haben ein 5 adriges Kabel auf welchem ist Strom

### 2. Assistent

Bei einem **5-adrigen Kabel** kann man **nicht sicher nur an der Farbe erkennen**, auf welcher Ader Strom liegt. Es muss gemessen werden.

Typische Belegung in Deutschland bei moderner Installation:

| Aderfarbe | Übliche Funktion |
|---|---|
| Grün/Gelb | Schutzleiter PE, darf nicht als stromführender Leiter genutzt werden |
| Blau | Neutralleiter N |
| Braun | Phase L1 |
| Schwarz | Phase L2 |
| Grau | Phase L3 |

Bei **Drehstrom/400 V** können also **braun, schwarz und grau stromführend** sein.

Bei einer normalen einphasigen Leitung kann es auch sein:

| Ader | Möglich |
|---|---|
| Braun | Dauerphase |
| Schwarz/Grau | geschaltete Phase, Korrespondierende, Reserve oder zweite Schaltung |
| Blau | Neutralleiter |
| Grün/Gelb | Schutzleiter |

Wichtig: **Blau kann bei falscher oder alter Installation ebenfalls Spannung führen.** Deshalb nie blind vertrauen.

Sichere Prüfung:

1. **Nicht anfassen, solange Spannung anliegen kann.**
2. Mit einem **zweipoligen Spannungsprüfer** messen, nicht mit Schraubendreher-Phasenprüfer.
3. Gegen **PE grün/gelb** und gegen **N blau** prüfen.
4. Erwartung:
   - Braun gegen Blau: ca. **230 V**
   - Schwarz gegen Blau: ggf. **230 V**
   - Grau gegen Blau: ggf. **230 V**
   - Braun/Schwarz/Grau untereinander: ggf. **400 V** bei Drehstrom
5. Vor Arbeiten: Sicherung/FI ausschalten, gegen Wiedereinschalten sichern, Spannungsfreiheit messen.

Wenn du mir ein Foto vom Kabel/Anschluss und sagst, ob es für **Herd, Lampe, Steckdose, Motor, Wärmepumpe oder Türsprechanlage** ist, kann ich dir die wahrscheinliche Belegung erklären. Arbeiten an 230/400 V aber nur durch Elektrofachkraft.
