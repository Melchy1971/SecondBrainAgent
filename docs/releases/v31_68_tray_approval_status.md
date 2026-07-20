# v31.68 Tray Approval Status

The Jarvis system-tray status now includes the current approval activity label,
including elevated and overdue counts. Pending decisions therefore remain
visible while the main desktop window is minimized.

The tray consumes only the cached, payload-free label produced by the native
approval refresh. It does not read the approval queue from the tray thread.
