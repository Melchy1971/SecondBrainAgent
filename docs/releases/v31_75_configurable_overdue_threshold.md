# v31.75 Configurable Overdue Threshold

The approval overdue threshold can now be configured with
`SECONDBRAIN_APPROVAL_OVERDUE_MINUTES`. Values from 1 through 1440 whole
minutes are accepted; missing, malformed or out-of-range values safely fall
back to the existing 15-minute default.

The threshold affects only the payload-free desktop urgency projection and its
notifications. Approval persistence, decisions and execution behavior remain
unchanged.
