---
title: "PrusaSlicer Ender 3 Max Neo"
type: chatgpt_conversation
source: chatgpt
source_id: "67b741ea-68cc-8007-af14-5a156f391d12"
created: 2025-02-20
tags:
  - chatgpt
  - import
  - ki
  - sap
---


# PrusaSlicer Ender 3 Max Neo

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `67b741ea-68cc-8007-af14-5a156f391d12`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

was muss ich in pursaslicer einstellen damit der druck perfekt mit einem sonic pad und ender 3 max neo läuft

### 2. Assistent

Für einen optimalen Druck mit deinem Ender 3 Max Neo in Kombination mit dem Sonic Pad solltest du in PrusaSlicer mehrere Bereiche anpassen:

### 1. Druckerprofil und Bauraum
- **Individuelles Profil anlegen:** Erstelle in PrusaSlicer ein neues Druckerprofil für den Ender 3 Max Neo. Trage die korrekten Maße (Druckbettgröße, maximale Bauhöhe etc.) ein – diese Angaben findest du in der Bedienungsanleitung oder auf der Herstellerseite.
- **Koordinaten und Ursprung:** Achte darauf, dass der Nullpunkt (0/0) an der linken Vorderseite deines Druckbetts liegt, falls dies der Standard bei deinem Gerät ist.

### 2. Start- und End-G-Code anpassen
Da das Sonic Pad in der Regel mit Klipper arbeitet, ist es wichtig, den G-Code so zu gestalten, dass er optimal mit der Firmware harmoniert. Ein Beispiel für einen angepassten Start-G-Code könnte folgendermaßen aussehen:
```
M140 S{first_layer_bed_temperature}  ; Bett vorheizen
M104 S{first_layer_temperature}       ; Extruder vorheizen
M109 S{first_layer_temperature}       ; Warte, bis Extruder die Temperatur erreicht
G28                                   ; Home aller Achsen
G29                                   ; Optional: Mesh-Bettnivellierung starten (falls installiert)
M420 S1                               ; Aktiviert die Bettnivellierung (wenn erforderlich)
```
Den End-G-Code kannst du ebenfalls anpassen, um etwaige Heizbefehle auszuschalten und den Druckkopf in eine sichere Position zu fahren. Diese Anpassungen verhindern Konflikte zwischen den im G-Code enthaltenen Befehlen und den Funktionen der Klipper-Firmware, die über das Sonic Pad gesteuert wird.

### 3. Retraction- und Druckgeschwindigkeiten
- **Retraction:** Da der Ender 3 in der Regel einen Bowden-Extruder verwendet, empfiehlt sich ein Retraction-Wert von ca. 6 bis 7 mm. Die Retraction-Geschwindigkeit liegt oft bei etwa 40–45 mm/s.
- **Druckgeschwindigkeit:** Ein Ausgangswert von ca. 60 mm/s ist oft ein guter Startpunkt. Je nach Modell und Filament kann es sinnvoll sein, diese Werte anzupassen, um Vibrationen und Druckartefakte zu minimieren.

### 4. Temperatur- und Kühlmanagement
- **Düsentemperatur:** Stelle die Düsentemperatur passend zum Filament ein (z. B. etwa 200 °C für PLA, 240 °C für ABS).
- **Betttemperatur:** Auch hier orientierst du dich am verwendeten Material (z. B. ca. 60 °C für PLA).
- **Kühlung:** Achte darauf, dass der Bauteilkühlventilator erst nach den ersten Schichten auf volle Leistung geht – das verbessert die Haftung der ersten Schicht und die Druckqualität insgesamt.

### 5. Feinjustierungen und Testdrucke
- **Layer-Höhe, Infill und Wandstärken:** Passe diese Parameter an dein Modell und deine Qualitätsansprüche an. 
- **Kalibrierung:** Es empfiehlt sich, mit Testdrucken zu starten, um kleinere Anpassungen (z. B. bei der Extrusion oder den Geschwindigkeiten) vorzunehmen.

Diese Einstellungen dienen als Ausgangspunkt. Je nach verwendetem Filament und spezifischen Gegebenheiten an deinem Arbeitsplatz können weitere Feinanpassungen nötig sein. Es ist auch sinnvoll, die Empfehlungen in den offiziellen Creality- oder Klipper-Foren sowie in der Dokumentation deines Sonic Pads zu prüfen.

Mit diesen Anpassungen in PrusaSlicer solltest du gute Voraussetzungen schaffen, um drucktechnisch optimale Ergebnisse mit deinem Ender 3 Max Neo und Sonic Pad zu erzielen.
