# PATCH P2.1.4 – Desktop Job Feedback

## Ziel
Desktop-Feedback für laufende Hintergrundjobs stabilisieren.

## Änderungen
- `secondbrain/desktop/job_feedback.py`
  - `JobState`
  - `JobFeedback`
  - `JobFeedbackCenter`
- Ereignis-Integration:
  - `JOB_STARTED`
  - `JOB_FINISHED`
  - `ERROR_OCCURRED`
- Notification-Integration:
  - Start = INFO
  - Erfolg = SUCCESS
  - Fehler = ERROR
  - Abbruch = WARNING
- Status-Integration:
  - idle = GREEN
  - running = YELLOW
  - failed = RED
- Tests:
  - Start
  - Progress Bounding
  - Success
  - Failure
  - Cancel
  - Active Filter
  - Unknown Job

## Validierung
`28 passed`

## Risiko
Niedrig. Kein UI-Toolkit gekoppelt. Reiner Service-Layer.
