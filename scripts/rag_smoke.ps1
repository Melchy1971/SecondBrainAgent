$ErrorActionPreference = "Stop"

$smokeRoot = Join-Path ($env:RUNNER_TEMP ?? $env:TEMP) "secondbrain-rag-smoke"
$commands = @(
    @("--project-root", $smokeRoot, "p1-rag-status"),
    @("--project-root", $smokeRoot, "p1-rag-ingest-text", "Jarvis RAG smoke evidence", "--source", "ci", "--title", "Smoke"),
    @("--project-root", $smokeRoot, "p1-rag-search", "Jarvis")
)

foreach ($arguments in $commands) {
    & python launcher.py @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "RAG smoke command failed with exit code ${LASTEXITCODE}: $($arguments -join ' ')"
    }
}
