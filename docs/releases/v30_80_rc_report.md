# Release-Candidate-Report v30.77.0

Bewertung: **CONDITIONAL_PASS**  
Erzeugt: 2026-07-08T13:52:54.795094+00:00  
Checks: 7 PASS / 8 WARN / 0 FAIL (gesamt 15)

## Bewertungsregel

BLOCKED bei mindestens einem FAIL; CONDITIONAL_PASS bei WARN ohne FAIL; sonst PASS. Hartregeln erzwingen BLOCKED: DEV_ONLY-Embeddings, fehlender Secret Vault, fehlende Connector Runtime.

## CheckÃ¼bersicht

| Check | Status | Kritisch | Zusammenfassung |
|-------|--------|----------|-----------------|
| version_sync | PASS | - | version 30.77.0 consistent |
| repo_doctor | WARN | - | structural check only |
| dependency_inventory | PASS | - | 8 requirement manifests, core deps present |
| pgvector_readiness | PASS | - | postgres driver available |
| embedding_provider | PASS | - | production embedding provider ollama |
| secret_vault | PASS | - | vault encrypt/health self-test passed |
| connector_runtime | PASS | - | connector runtime defined (registry + connectors) |
| native_desktop | WARN | - | native desktop package present (not runtime-verified) |
| agent_safety | WARN | - | agent safety package present (not runtime-verified) |
| workflow_engine | WARN | - | workflow engine package present (not runtime-verified) |
| memory_injection | WARN | - | memory injection package present (not runtime-verified) |
| scheduler | WARN | - | scheduler / background-agent runtime present (not runtime-verified) |
| plugin_runtime | PASS | - | plugin manifest present |
| installer_build | WARN | - | installer assets present (not built here) |
| pytest | WARN | - | full suite not executed by the gate |
## Bedingungen (WARN)

- **repo_doctor**: structural check only â€” run `launcher.py doctor` under Python 3.11 for the authoritative result
- **native_desktop** (`secondbrain/native`): native desktop package present (not runtime-verified) â€” verify native_desktop under Python 3.11 before tagging
- **agent_safety** (`secondbrain/agent/safety`): agent safety package present (not runtime-verified) â€” verify agent_safety under Python 3.11 before tagging
- **workflow_engine** (`secondbrain/agent/workflow`): workflow engine package present (not runtime-verified) â€” verify workflow_engine under Python 3.11 before tagging
- **memory_injection** (`secondbrain/agent/memory_injection`): memory injection package present (not runtime-verified) â€” verify memory_injection under Python 3.11 before tagging
- **scheduler** (`secondbrain/agent/background_agents`): scheduler / background-agent runtime present (not runtime-verified) â€” verify scheduler under Python 3.11 before tagging
- **installer_build** (`packaging/windows/`): installer assets present (not built here) â€” run packaging/windows/build.ps1 on Windows and attach the artifacts
- **pytest** (`tests/`): full suite not executed by the gate â€” run `pytest` under Python 3.11 and attach the summary before tagging

