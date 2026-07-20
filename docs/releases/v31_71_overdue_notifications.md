# v31.71 Overdue Approval Notifications

Jarvis now emits a dedicated tray notification when visible approvals cross
the 15-minute overdue threshold. This covers urgency changes that happen while
the pending approval count itself remains unchanged.

The first valid snapshot only establishes the overdue baseline. Unavailable,
unchanged or decreasing counts do not trigger notifications, and messages
contain only aggregate counts.
