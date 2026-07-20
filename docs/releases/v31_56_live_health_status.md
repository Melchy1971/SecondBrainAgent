# v31.56 Live Health Status

The native Jarvis desktop status panel now derives its database, embedding and
Ollama labels from the existing bootstrap health checks instead of displaying
static placeholders.

The projection is deliberately allowlisted. It exposes only normalized status
labels and never forwards connection strings, hosts, model names, environment
variable names or provider error details to the desktop surface.
