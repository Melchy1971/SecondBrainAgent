# v31.59 Live Alert Status

The native Jarvis alert panel now derives its embedding, PostgreSQL, Ollama and
queue labels from the existing health and job snapshots. Pending and retry jobs
are combined while blocked jobs remain visible as a separate count.

pgvector is explicitly shown as `Not checked`: the lightweight desktop refresh
does not open a database connection or imply production readiness without the
dedicated live gate. Labels are allowlisted and never expose job payloads or
database connection details.
