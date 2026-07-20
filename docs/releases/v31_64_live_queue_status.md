# v31.64 Live Queue Status

The native Jarvis queue info row, alert and metric ring now share a lightweight
workspace-local job snapshot refreshed every two seconds. Pending and retry jobs
are combined, while running and blocked jobs contribute to the active count.

The ring shows the active job count with a binary activity arc because the queue
has no fixed capacity. Job payloads and completed-job counts are not projected
into this surface.
