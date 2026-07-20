# v31.70 Approval Notifications

Jarvis now emits a payload-free system-tray notification when the number of
pending approvals increases. The first snapshot only establishes a baseline;
unchanged or decreasing counts remain silent to prevent notification noise.

Notifications contain only the number of newly waiting decisions. Optional
tray-backend failures are contained and do not interrupt the desktop refresh.
