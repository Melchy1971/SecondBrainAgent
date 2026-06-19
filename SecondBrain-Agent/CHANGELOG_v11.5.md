# CHANGELOG v11.5 – Mobile Bridge

## Added
- Local-first Mobile Bridge Runtime.
- Device Registry for iOS, Android, Web and Desktop companion clients.
- Push Outbox as persistent JSON queue.
- Mobile Capture Inbox for notes, voice notes, URLs, tasks and photo notes.
- Approval Inbox with trusted-device guard.
- Launcher commands for mobile registration, push, capture and approvals.

## Architecture
Mobile clients do not execute actions directly. They submit captures, receive queued notifications and decide approval requests. Execution remains governed by the local runtime.
