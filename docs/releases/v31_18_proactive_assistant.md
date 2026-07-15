# Jarvis v31.18 Proaktive Assistenz

Die vorhandene Suggestion Engine erkennt die geforderten Standardkategorien, bewertet sie nachvollziehbar und persistiert Rules, Suggestions und Feedback im produktiven PostgreSQL-Pfad.

Sicherheitsinvarianten:

- Jede Suggestion zeigt Evidenz und Confidence.
- Niedrige Confidence wird nicht kritisch markiert.
- Vorschlaege werden dedupliziert, begrenzt und durch Cooldowns kontrolliert.
- Secrets und sensible Vorschautexte werden redigiert.
- Accept fuehrt keine E-Mail-, Kalender-, Datei-, Connector- oder Berechtigungsaktion direkt aus.
- Feedback kann Security Policy, Approval und Privacy Mode nicht veraendern.
- Workspace Crossing wird durch Repository-Keys und workspacegebundene Abfragen verhindert.

Die fokussierten Engine-, Dashboard- und Repository-Tests sind gruen. Ein echter PostgreSQL-Test erfordert eine isolierte `TEST_DATABASE_URL`.
