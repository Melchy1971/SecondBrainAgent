# v31.89 German Calendar Time Resolution

Calendar creation now resolves a deliberately small German date/time grammar
before creating a persistent approval. Supported forms include timezone-aware
ISO timestamps, `heute`, `morgen`, `übermorgen`/`uebermorgen`, and explicit
`DD.MM.YYYY` dates with numeric times such as `morgen um 14 Uhr` or
`24.07.2026 um 8:30 Uhr`.

The default timezone is `Europe/Berlin` and can be changed with
`SECONDBRAIN_CALENDAR_TIMEZONE`. The core runtime now includes `tzdata` so the
IANA timezone remains available on Windows and daylight-saving transitions are
evaluated correctly.

The resolver never guesses written number words, past natural times, invalid
zones, or ambiguous/non-existent daylight-saving times. In those cases Jarvis
reopens the bound `when` slot, creates no approval, and asks for a corrected,
unambiguous time. The normalized timezone-aware start and one-hour end remain
covered by the existing payload hash, workspace binding, and single-use lease.
