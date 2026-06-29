---
title: "Supabase Passwortschutz aktivieren"
type: chatgpt_conversation
source: chatgpt
source_id: "68dfa092-4234-8328-b06a-bb0d2f1f0dbc"
created: 2025-10-03
tags:
  - chatgpt
  - code
  - import
  - ki
  - projekt
  - sap
---


# Supabase Passwortschutz aktivieren

## Metadaten

- Quelle: ChatGPT Export
- Conversation ID: `68dfa092-4234-8328-b06a-bb0d2f1f0dbc`
- Nachrichten: 2

## Kurzüberblick

Automatisch importierte ChatGPT-Unterhaltung. Für eine KI-Zusammenfassung später AI Review ausführen.

## Unterhaltung

### 1. Benutzer

supabase: wie mach ich das: Verbleibende erforderliche Aktion: Sie müssen den Schutz vor Passwortlecks in Ihrem Supabase-Dashboard manuell aktivieren: 


Gehen Sie zu den Authentifizierungseinstellungen

Aktivieren Sie „Benutzer daran hindern, Passwörter festzulegen, die durchgesickert sind“.

### 2. Assistent

Kurz & knackig – so aktivierst du den „Passwort-Leaks“-Schutz in Supabase:

1) In dein Projekt gehen → links **Authentication**.  
2) Oben **Settings** öffnen (ggf. Tab „Security“/„Password Security“).  
3) Den Schalter **“Prevent users from setting leaked passwords”** (dt. sinngemäß: *„Benutzer daran hindern, durchgesickerte Passwörter zu setzen“*) **einschalten**.  
4) **Save**. Fertig.  
Hinter den Kulissen nutzt Supabase dafür die HaveIBeenPwned-Datenbank (Pwned Passwords). citeturn1view0

Wichtige Hinweise, damit du nicht stolperst:
- **Plan-Voraussetzung:** Der Leaks-Schutz ist erst **ab Pro-Plan** aktivierbar. Auf Free siehst du die Warnung im Security Advisor, kannst sie aber nicht schalten. citeturn1view0turn3search7  
- **Wie es geprüft wird:** Supabase prüft Passwörter gegen HIBP und blockt bekannte Leaks; das ist in den Docs so beschrieben. citeturn1view0turn4search1turn4search0  
- **OAuth-only Projekte:** Wenn du **keine Passwort-Anmeldungen** verwendest (nur Google, GitHub etc.), ist die Advisor-Warnung nicht wirklich relevant. Es gibt aktuelle Threads dazu. citeturn0search13

Schnelltest (für dein Dev-System): Versuch eine Registrierung mit einem sehr gängigen Passwort (z. B. „Password123!“). Bei aktivem Schutz bekommst du clientseitig einen **`weak_password`**-Fehler, meist mit Grund **`"pwned"`**. So weißt du, dass der Toggle wirkt. citeturn5search0

Bonus-Härtung (wenn du schon im Menü bist):
- **Mindestlänge** hochsetzen und **Zeichenklassen** erzwingen. citeturn1view0
- **MFA** aktivieren, wo sinnvoll. citeturn1view0

Wenn du mir sagst, welchen Plan ihr nutzt und welche Login-Flows (Passwort vs. nur OAuth), gebe ich dir eine kurze, maßgeschneiderte Checkliste für eure Einstellungskombination.
