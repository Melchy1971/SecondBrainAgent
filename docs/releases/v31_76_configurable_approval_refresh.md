# v31.76 Configurable Approval Refresh

The native approval polling interval can now be configured with
`SECONDBRAIN_APPROVAL_REFRESH_SECONDS`. Whole-second values from 1 through 60
are accepted. Missing, malformed or out-of-range values retain the existing
two-second default.

The initial desktop refresh remains unchanged, while subsequent approval
snapshots use the validated interval. This prevents accidental tight polling
and does not alter approval persistence or access boundaries.
