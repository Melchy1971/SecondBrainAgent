# Proaktive Assistenz v31.18

Die Implementierung erweitert `SecondBrain/proactive` und verwendet Tasks, Planner v2, Briefings, Kalender-/Mail-Kontext, Approval Inbox, Connector-/Backup-Health, Memory, Knowledge und Jobstatus ausschließlich als Eingaben. Sie fuehrt keine riskante Aktion selbst aus.

Suggestions enthalten Workspace, Kategorie, Evidenz, Confidence, Prioritaet, vorgeschlagene Aktion, Quellen, Lebenszyklus und Version. Rules steuern Aktivierung, Bedingungen, Confidence-Schwelle, Minuten-Cooldown, Prioritaet, Maximalzahl und Workspace Scope.

Der Score kombiniert Dringlichkeit, Auswirkung, Confidence, Evidenzqualitaet, Nutzerpraeferenz, Feedback, Wiederholung und Arbeitslast. Dedup Keys, Cooldowns und Kategorie-Limits verhindern Suggestion-Fluten. Niedrige Confidence wird nie kritisch dargestellt. Titel, Evidenz und Feedbackdetails werden redigiert.

Accept darf lokale Tasks, Plaene, Reviews, Briefings und Reminder vorbereiten. Externe Writes werden in Review-/Approval-Intents umgewandelt und nie direkt ausgefuehrt.

`PostgresProactiveRepository` speichert Suggestions, Rule-Zustand und Feedback workspaceisoliert. In-Memory-Betrieb ist nur Entwicklung; Produktion blockiert ohne PostgreSQL. Feedback beeinflusst Ranking und Cooldown, besitzt aber keinen Zugriff auf Security Policy, Approval oder Privacy Mode.
