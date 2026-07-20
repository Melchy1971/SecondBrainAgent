# v31.61 Live Storage Alerts

The native Jarvis alert panel now replaces its Backup and Vector Index
placeholders with existing local status sources. Backup state comes from the
read-only Backup Center snapshot. Vector state is projected from the latest
P1 RAG validation report without initializing or mutating the RAG store.

Missing reports and snapshots produce explicit `Not checked` or `Unavailable`
labels. Archive paths, validation findings and other payload details never reach
the alert panel.
